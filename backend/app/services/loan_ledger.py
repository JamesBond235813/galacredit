from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan
from app.models.loan_installment import LoanInstallment
from app.models.loan_transaction import LoanTransaction
from app.services.loan_amounts import (
    calculate_installment_amounts,
    calculate_guarantee_fee_amount,
    calculate_installment_periods,
    calculate_interest_amount,
    resolve_interest_rate,
    round_money,
)


ACTIVE_LEDGER_STATUSES = {"DISBURSED", "OVERDUE", "SETTLED"}
TRANSACTION_TYPE_LABELS = {
    "DISBURSEMENT": "放款",
    "REPAYMENT": "收款登记",
    "REDUCTION": "减免登记",
    "SETTLEMENT": "结清补录",
    "OTHER_FEE": "其他费用",
}


def _get_loaded_relation(entity: Any, relation_name: str):
    """读取已加载关系，避免在异步上下文外触发懒加载。

    :param entity: ORM 实体对象
    :param relation_name: 关系字段名
    :return: 已加载的关系值，未加载时返回 None
    """
    if entity is None:
        return None
    state = getattr(entity, "__dict__", {})
    return state.get(relation_name)


def _to_cents(value: Any) -> int:
    return int(round(float(value or 0) * 100))


def _from_cents(value: int) -> float:
    return round(value / 100, 2)


def split_money(total_amount: Any, parts: int) -> List[float]:
    if parts <= 0:
        return []

    total_cents = _to_cents(total_amount)
    base = total_cents // parts
    remainder = total_cents - base * parts
    return [_from_cents(base + (1 if index < remainder else 0)) for index in range(parts)]


def split_money_by_weights(total_amount: Any, weights: Dict[str, Any]) -> Dict[str, float]:
    total_cents = _to_cents(total_amount)
    prepared = []
    for key, value in (weights or {}).items():
        cents = max(_to_cents(value), 0)
        if cents > 0:
            prepared.append((key, cents))

    if total_cents <= 0 or not prepared:
        return {key: 0.0 for key in (weights or {})}

    total_weight = sum(item[1] for item in prepared)
    allocated = {}
    used = 0
    remainders = []

    for key, cents in prepared:
        raw = total_cents * cents / total_weight
        base = int(raw)
        allocated[key] = base
        used += base
        remainders.append((raw - base, key))

    remaining = total_cents - used
    remainders.sort(key=lambda item: (-item[0], item[1]))
    for index in range(remaining):
        allocated[remainders[index % len(remainders)][1]] += 1

    return {key: _from_cents(allocated.get(key, 0)) for key in (weights or {})}


def build_installment_due_date(disbursed_at: datetime, period_no: int) -> datetime:
    return disbursed_at + timedelta(days=period_no - 1)


def build_installment_blueprint(loan: Loan) -> List[Dict[str, Any]]:
    if not getattr(loan, "term_days", None) or not getattr(loan, "disbursed_at", None):
        return []

    try:
        periods = max(int(getattr(loan, "installment_count", 0) or 0), 1)
        if not getattr(loan, "total_repayment_amount_snapshot", 0):
            periods = calculate_installment_periods(loan.term_days)
    except (TypeError, ValueError):
        return []

    snapshot_total = round_money(getattr(loan, "total_repayment_amount_snapshot", 0))
    if snapshot_total > 0:
        amounts = calculate_installment_amounts(
            snapshot_total,
            getattr(loan, "installment_ratios_json", None),
            periods,
        )
        items = []
        total_days = max(int(getattr(loan, "term_days", 1) or 1), 1)
        for index, due_amount in enumerate(amounts):
            due_day = max(1, round(total_days * (index + 1) / periods))
            due_date = loan.disbursed_at + timedelta(days=due_day)
            if index == periods - 1 and loan.due_date:
                due_date = loan.due_date
            items.append(
                {
                    "period_no": index + 1,
                    "due_date": due_date,
                    "principal_amount": due_amount,
                    "interest_amount": 0.0,
                    "guarantee_fee_amount": 0.0,
                    "due_amount": due_amount,
                }
            )
        return items

    principal_parts = split_money(getattr(loan, "credit_limit", 0), periods)
    interest_total = calculate_interest_amount(
        getattr(loan, "credit_limit", 0),
        getattr(loan, "term_days", 0),
        getattr(loan, "interest_start_day", 1),
        getattr(loan, "repayment_due_day", getattr(loan, "term_days", 0)),
        resolve_interest_rate(loan),
    )
    interest_parts = split_money(interest_total, periods)
    guarantee_total = calculate_guarantee_fee_amount(
        getattr(loan, "fee_amount", 0),
        getattr(loan, "credit_limit", 0),
        getattr(loan, "term_days", 0),
        getattr(loan, "interest_start_day", 1),
        getattr(loan, "repayment_due_day", getattr(loan, "term_days", 0)),
        resolve_interest_rate(loan),
    )
    guarantee_parts = split_money(guarantee_total, periods)

    items = []
    for index in range(periods):
        principal_amount = round_money(principal_parts[index] if index < len(principal_parts) else 0)
        interest_amount = round_money(interest_parts[index] if index < len(interest_parts) else 0)
        guarantee_fee_amount = round_money(guarantee_parts[index] if index < len(guarantee_parts) else 0)
        items.append(
            {
                "period_no": index + 1,
                "due_date": loan.due_date or build_installment_due_date(loan.disbursed_at, int(getattr(loan, "term_days", 1) or 1)),
                "principal_amount": principal_amount,
                "interest_amount": interest_amount,
                "guarantee_fee_amount": guarantee_fee_amount,
                "due_amount": round_money(principal_amount + interest_amount + guarantee_fee_amount),
            }
        )
    return items


async def ensure_installment_records_async(db: AsyncSession, loan: Loan) -> List[LoanInstallment]:
    if loan.status not in ACTIVE_LEDGER_STATUSES:
        return _get_loaded_relation(loan, "installments") or []
    if not getattr(loan, "disbursed_at", None) or not getattr(loan, "term_days", None):
        return _get_loaded_relation(loan, "installments") or []

    # 显式查询分期记录，避免访问关系属性触发懒加载导致 MissingGreenlet。
    existing_items = (
        await db.execute(
            select(LoanInstallment)
            .where(LoanInstallment.loan_id == loan.id)
            .order_by(LoanInstallment.period_no.asc())
        )
    ).scalars().all()
    if existing_items:
        loan.installments = existing_items
        return existing_items

    items = []
    for blueprint in build_installment_blueprint(loan):
        installment = LoanInstallment(
            loan_id=loan.id,
            period_no=blueprint["period_no"],
            due_date=blueprint["due_date"],
            status="PENDING",
            principal_amount=blueprint["principal_amount"],
            interest_amount=blueprint["interest_amount"],
            guarantee_fee_amount=blueprint["guarantee_fee_amount"],
            due_amount=blueprint["due_amount"],
        )
        db.add(installment)
        items.append(installment)

    await db.flush()
    loan.installments = sorted(items, key=lambda item: item.period_no)

    existing_repaid_amount = round_money(getattr(loan, "repaid_amount", 0))
    existing_reduction_amount = round_money(getattr(loan, "reduction_amount", 0))
    if existing_repaid_amount > 0 or existing_reduction_amount > 0:
        penalty_total = round_money(getattr(loan, "penalty_amount", 0))

        paid_penalty_amount = min(existing_repaid_amount, penalty_total)
        loan.paid_penalty_amount = round_money(max(getattr(loan, "paid_penalty_amount", 0), paid_penalty_amount))
        _apply_paid_amount_to_installments(loan.installments, round_money(existing_repaid_amount - paid_penalty_amount))

        reduced_penalty_amount = min(
            existing_reduction_amount,
            max(penalty_total - loan.paid_penalty_amount, 0),
        )
        loan.reduced_penalty_amount = round_money(
            max(getattr(loan, "reduced_penalty_amount", 0), reduced_penalty_amount)
        )
        _apply_reduction_amount_to_installments(
            loan.installments,
            round_money(existing_reduction_amount - reduced_penalty_amount),
        )

        sync_installment_records(loan)

    return loan.installments


def _build_virtual_installment_rows(loan: Loan) -> List[Dict[str, Any]]:
    rows = []
    for blueprint in build_installment_blueprint(loan):
        rows.append(
            {
                **blueprint,
                "status": "PENDING",
                "paid_principal_amount": 0.0,
                "paid_interest_amount": 0.0,
                "paid_guarantee_fee_amount": 0.0,
                "paid_amount": 0.0,
                "reduced_principal_amount": 0.0,
                "reduced_interest_amount": 0.0,
                "reduced_guarantee_fee_amount": 0.0,
                "reduction_amount": 0.0,
                "remaining_amount": blueprint["due_amount"],
                "settled_at": None,
            }
        )
    return rows


def _component_outstanding(row: Dict[str, Any]) -> Dict[str, float]:
    return {
        "principal_amount": round_money(
            row["principal_amount"] - row.get("paid_principal_amount", 0) - row.get("reduced_principal_amount", 0)
        ),
        "interest_amount": round_money(
            row["interest_amount"] - row.get("paid_interest_amount", 0) - row.get("reduced_interest_amount", 0)
        ),
        "guarantee_fee_amount": round_money(
            row["guarantee_fee_amount"]
            - row.get("paid_guarantee_fee_amount", 0)
            - row.get("reduced_guarantee_fee_amount", 0)
        ),
    }


def _apply_amount_to_rows(rows: List[Dict[str, Any]], amount: Any, target: str) -> Dict[str, float]:
    remaining = round_money(amount)
    components = {
        "principal_amount": 0.0,
        "interest_amount": 0.0,
        "guarantee_fee_amount": 0.0,
    }

    if remaining <= 0:
        return components

    for row in rows:
        if remaining <= 0:
            break

        outstanding = round_money(row["due_amount"] - row.get("paid_amount", 0) - row.get("reduction_amount", 0))
        if outstanding <= 0:
            continue

        current_amount = min(remaining, outstanding)
        allocated = split_money_by_weights(current_amount, _component_outstanding(row))

        if target == "paid":
            row["paid_principal_amount"] = round_money(row.get("paid_principal_amount", 0) + allocated["principal_amount"])
            row["paid_interest_amount"] = round_money(row.get("paid_interest_amount", 0) + allocated["interest_amount"])
            row["paid_guarantee_fee_amount"] = round_money(
                row.get("paid_guarantee_fee_amount", 0) + allocated["guarantee_fee_amount"]
            )
            row["paid_amount"] = round_money(row.get("paid_amount", 0) + current_amount)
        else:
            row["reduced_principal_amount"] = round_money(
                row.get("reduced_principal_amount", 0) + allocated["principal_amount"]
            )
            row["reduced_interest_amount"] = round_money(
                row.get("reduced_interest_amount", 0) + allocated["interest_amount"]
            )
            row["reduced_guarantee_fee_amount"] = round_money(
                row.get("reduced_guarantee_fee_amount", 0) + allocated["guarantee_fee_amount"]
            )
            row["reduction_amount"] = round_money(row.get("reduction_amount", 0) + current_amount)

        row["remaining_amount"] = round_money(row["due_amount"] - row.get("paid_amount", 0) - row.get("reduction_amount", 0))
        remaining = round_money(remaining - current_amount)

        components["principal_amount"] = round_money(components["principal_amount"] + allocated["principal_amount"])
        components["interest_amount"] = round_money(components["interest_amount"] + allocated["interest_amount"])
        components["guarantee_fee_amount"] = round_money(
            components["guarantee_fee_amount"] + allocated["guarantee_fee_amount"]
        )

    return components


def _sync_row_statuses(rows: List[Dict[str, Any]], now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    current_time = now or datetime.now()
    assigned_current = False

    for row in rows:
        remaining_amount = round_money(row["due_amount"] - row.get("paid_amount", 0) - row.get("reduction_amount", 0))
        row["remaining_amount"] = remaining_amount

        if remaining_amount <= 0:
            row["status"] = "SETTLED"
            row["settled_at"] = row.get("settled_at") or current_time
            continue

        row["settled_at"] = None
        if row["due_date"] < current_time:
            row["status"] = "OVERDUE"
            continue

        if not assigned_current:
            row["status"] = "CURRENT"
            assigned_current = True
        else:
            row["status"] = "PENDING"

    return rows


def build_virtual_installments(loan: Loan, now: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    rows = _build_virtual_installment_rows(loan)
    payment_total = round_money(getattr(loan, "repaid_amount", 0))
    reduction_total = round_money(getattr(loan, "reduction_amount", 0))
    penalty_total = round_money(getattr(loan, "penalty_amount", 0))

    paid_penalty_amount = min(payment_total, penalty_total)
    payment_total = round_money(payment_total - paid_penalty_amount)

    reduced_penalty_amount = min(reduction_total, max(penalty_total - paid_penalty_amount, 0))
    reduction_total = round_money(reduction_total - reduced_penalty_amount)

    paid_components = _apply_amount_to_rows(rows, payment_total, "paid")
    reduced_components = _apply_amount_to_rows(rows, reduction_total, "reduced")

    _sync_row_statuses(rows, now=now)
    return rows, {
        "paid_penalty_amount": round_money(paid_penalty_amount),
        "reduced_penalty_amount": round_money(reduced_penalty_amount),
        **paid_components,
        "reduced_principal_amount": round_money(reduced_components["principal_amount"]),
        "reduced_interest_amount": round_money(reduced_components["interest_amount"]),
        "reduced_guarantee_fee_amount": round_money(reduced_components["guarantee_fee_amount"]),
    }


def sync_installment_records(loan: Loan, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    current_time = now or datetime.now()
    loaded_installments = _get_loaded_relation(loan, "installments") or []
    rows = []
    for item in sorted(loaded_installments, key=lambda current: current.period_no):
        paid_amount = round_money(
            getattr(item, "paid_amount", 0)
            or (
                getattr(item, "paid_principal_amount", 0)
                + getattr(item, "paid_interest_amount", 0)
                + getattr(item, "paid_guarantee_fee_amount", 0)
            )
        )
        reduction_amount = round_money(
            getattr(item, "reduction_amount", 0)
            or (
                getattr(item, "reduced_principal_amount", 0)
                + getattr(item, "reduced_interest_amount", 0)
                + getattr(item, "reduced_guarantee_fee_amount", 0)
            )
        )
        rows.append(
            {
                "id": item.id,
                "period_no": item.period_no,
                "due_date": item.due_date,
                "status": item.status,
                "principal_amount": round_money(item.principal_amount),
                "interest_amount": round_money(item.interest_amount),
                "guarantee_fee_amount": round_money(item.guarantee_fee_amount),
                "due_amount": round_money(item.due_amount),
                "paid_principal_amount": round_money(item.paid_principal_amount),
                "paid_interest_amount": round_money(item.paid_interest_amount),
                "paid_guarantee_fee_amount": round_money(item.paid_guarantee_fee_amount),
                "paid_amount": paid_amount,
                "reduced_principal_amount": round_money(item.reduced_principal_amount),
                "reduced_interest_amount": round_money(item.reduced_interest_amount),
                "reduced_guarantee_fee_amount": round_money(item.reduced_guarantee_fee_amount),
                "reduction_amount": reduction_amount,
                "settled_at": item.settled_at,
                "remaining_amount": round_money(item.due_amount - paid_amount - reduction_amount),
            }
        )

    _sync_row_statuses(rows, now=current_time)

    row_map = {row["id"]: row for row in rows}
    for item in loaded_installments:
        row = row_map.get(item.id)
        if not row:
            continue
        item.status = row["status"]
        item.paid_amount = row["paid_amount"]
        item.reduction_amount = row["reduction_amount"]
        item.settled_at = row["settled_at"]

    return rows


def serialize_installment_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("id"),
        "period_no": int(row.get("period_no", 0)),
        "due_date": row.get("due_date"),
        "status": row.get("status") or "PENDING",
        "principal_amount": round_money(row.get("principal_amount", 0)),
        "interest_amount": round_money(row.get("interest_amount", 0)),
        "guarantee_fee_amount": round_money(row.get("guarantee_fee_amount", 0)),
        "due_amount": round_money(row.get("due_amount", 0)),
        "paid_amount": round_money(row.get("paid_amount", 0)),
        "reduction_amount": round_money(row.get("reduction_amount", 0)),
        "remaining_amount": round_money(row.get("remaining_amount", 0)),
        "paid_principal_amount": round_money(row.get("paid_principal_amount", 0)),
        "paid_interest_amount": round_money(row.get("paid_interest_amount", 0)),
        "paid_guarantee_fee_amount": round_money(row.get("paid_guarantee_fee_amount", 0)),
        "reduced_principal_amount": round_money(row.get("reduced_principal_amount", 0)),
        "reduced_interest_amount": round_money(row.get("reduced_interest_amount", 0)),
        "reduced_guarantee_fee_amount": round_money(row.get("reduced_guarantee_fee_amount", 0)),
        "settled_at": row.get("settled_at"),
    }


def build_loan_fund_flow_summary(
    loan: Loan,
    installments: List[Dict[str, Any]],
    penalty_paid_amount: Any = None,
    penalty_reduced_amount: Any = None,
) -> Dict[str, Any]:
    expected_principal_amount = round_money(sum(item["principal_amount"] for item in installments))
    expected_interest_amount = round_money(sum(item["interest_amount"] for item in installments))
    expected_guarantee_fee_amount = round_money(sum(item["guarantee_fee_amount"] for item in installments))

    paid_principal_amount = round_money(sum(item["paid_principal_amount"] for item in installments))
    paid_interest_amount = round_money(sum(item["paid_interest_amount"] for item in installments))
    paid_guarantee_fee_amount = round_money(sum(item["paid_guarantee_fee_amount"] for item in installments))

    reduced_principal_amount = round_money(sum(item["reduced_principal_amount"] for item in installments))
    reduced_interest_amount = round_money(sum(item["reduced_interest_amount"] for item in installments))
    reduced_guarantee_fee_amount = round_money(sum(item["reduced_guarantee_fee_amount"] for item in installments))

    penalty_amount = round_money(getattr(loan, "penalty_amount", 0))
    paid_penalty_amount = round_money(
        getattr(loan, "paid_penalty_amount", 0) if penalty_paid_amount is None else penalty_paid_amount
    )
    reduced_penalty_amount = round_money(
        getattr(loan, "reduced_penalty_amount", 0) if penalty_reduced_amount is None else penalty_reduced_amount
    )

    principal_balance_amount = round_money(
        max(expected_principal_amount - paid_principal_amount - reduced_principal_amount, 0)
    )
    fee_balance_amount = round_money(
        max(
            expected_interest_amount
            + expected_guarantee_fee_amount
            - paid_interest_amount
            - paid_guarantee_fee_amount
            - reduced_interest_amount
            - reduced_guarantee_fee_amount,
            0,
        )
    )
    penalty_balance_amount = round_money(max(penalty_amount - paid_penalty_amount - reduced_penalty_amount, 0))
    overdue_installment_count = len([item for item in installments if item["status"] == "OVERDUE"])
    next_unsettled = next((item for item in installments if item["remaining_amount"] > 0), None)

    expected_income_amount = round_money(expected_interest_amount + expected_guarantee_fee_amount + penalty_amount)
    realized_income_amount = round_money(
        paid_interest_amount + paid_guarantee_fee_amount + paid_penalty_amount
    )
    reduced_fee_amount = round_money(
        reduced_interest_amount + reduced_guarantee_fee_amount + reduced_penalty_amount
    )

    return {
        "installment_periods": len(installments),
        "expected_principal_amount": expected_principal_amount,
        "expected_interest_amount": expected_interest_amount,
        "expected_guarantee_fee_amount": expected_guarantee_fee_amount,
        "expected_income_amount": expected_income_amount,
        "paid_principal_amount": paid_principal_amount,
        "paid_interest_amount": paid_interest_amount,
        "paid_guarantee_fee_amount": paid_guarantee_fee_amount,
        "paid_penalty_amount": paid_penalty_amount,
        "realized_income_amount": realized_income_amount,
        "reduced_principal_amount": reduced_principal_amount,
        "reduced_interest_amount": reduced_interest_amount,
        "reduced_guarantee_fee_amount": reduced_guarantee_fee_amount,
        "reduced_penalty_amount": reduced_penalty_amount,
        "reduced_fee_amount": reduced_fee_amount,
        "principal_balance_amount": principal_balance_amount,
        "fee_balance_amount": fee_balance_amount,
        "penalty_amount": penalty_amount,
        "penalty_balance_amount": penalty_balance_amount,
        "remaining_amount": round_money(principal_balance_amount + fee_balance_amount + penalty_balance_amount),
        "overdue_installment_count": overdue_installment_count,
        "current_installment_period": next_unsettled["period_no"] if next_unsettled else None,
        "next_due_date": next_unsettled["due_date"] if next_unsettled else None,
    }


def get_loan_ledger_snapshot(
    loan: Loan,
    now: Optional[datetime] = None,
    sync_models: bool = False,
) -> Dict[str, Any]:
    loaded_installments = _get_loaded_relation(loan, "installments") or []
    if loaded_installments:
        rows = sync_installment_records(loan, now=now) if sync_models else []
        if not rows:
            rows = []
            for item in sorted(loaded_installments, key=lambda current: current.period_no):
                rows.append(
                    {
                        "id": item.id,
                        "period_no": item.period_no,
                        "due_date": item.due_date,
                        "status": item.status,
                        "principal_amount": round_money(item.principal_amount),
                        "interest_amount": round_money(item.interest_amount),
                        "guarantee_fee_amount": round_money(item.guarantee_fee_amount),
                        "due_amount": round_money(item.due_amount),
                        "paid_principal_amount": round_money(item.paid_principal_amount),
                        "paid_interest_amount": round_money(item.paid_interest_amount),
                        "paid_guarantee_fee_amount": round_money(item.paid_guarantee_fee_amount),
                        "paid_amount": round_money(item.paid_amount),
                        "reduced_principal_amount": round_money(item.reduced_principal_amount),
                        "reduced_interest_amount": round_money(item.reduced_interest_amount),
                        "reduced_guarantee_fee_amount": round_money(item.reduced_guarantee_fee_amount),
                        "reduction_amount": round_money(item.reduction_amount),
                        "settled_at": item.settled_at,
                        "remaining_amount": round_money(item.due_amount - item.paid_amount - item.reduction_amount),
                    }
                )
            _sync_row_statuses(rows, now=now)

        return {
            "installments": [serialize_installment_row(item) for item in rows],
            "summary": build_loan_fund_flow_summary(loan, rows),
        }

    rows, virtual_meta = build_virtual_installments(loan, now=now)
    return {
        "installments": [serialize_installment_row(item) for item in rows],
        "summary": build_loan_fund_flow_summary(
            loan,
            rows,
            penalty_paid_amount=virtual_meta["paid_penalty_amount"],
            penalty_reduced_amount=virtual_meta["reduced_penalty_amount"],
        ),
    }


def sync_loan_repayment_state(loan: Loan, now: Optional[datetime] = None) -> str:
    if loan.status not in ACTIVE_LEDGER_STATUSES:
        return loan.status

    loaded_installments = _get_loaded_relation(loan, "installments") or []
    ledger = get_loan_ledger_snapshot(loan, now=now, sync_models=bool(loaded_installments))
    summary = ledger["summary"]

    if summary["remaining_amount"] <= 0:
        loan.status = "SETTLED"
        loan.repay_attempt_count = 0
    elif summary["overdue_installment_count"] > 0 and not bool(getattr(loan, "overdue_hidden", False)):
        loan.status = "OVERDUE"
    else:
        loan.status = "DISBURSED"
    return loan.status


def serialize_transaction(transaction: LoanTransaction) -> Dict[str, Any]:
    return {
        "id": transaction.id,
        "transaction_type": transaction.transaction_type,
        "transaction_label": TRANSACTION_TYPE_LABELS.get(transaction.transaction_type, transaction.transaction_type),
        "amount": round_money(transaction.amount),
        "principal_amount": round_money(transaction.principal_amount),
        "interest_amount": round_money(transaction.interest_amount),
        "guarantee_fee_amount": round_money(transaction.guarantee_fee_amount),
        "penalty_amount": round_money(transaction.penalty_amount),
        "operator_name": transaction.operator_name,
        "note": transaction.note,
        "created_at": transaction.created_at,
    }


async def create_disbursement_transaction_async(
    db: AsyncSession,
    loan: Loan,
    operator_name: Optional[str] = None,
    note: Optional[str] = None,
) -> LoanTransaction:
    disbursement_amount = round_money(
        getattr(loan, "actual_disbursement_amount", 0)
        if getattr(loan, "total_repayment_amount_snapshot", 0)
        else getattr(loan, "credit_limit", 0)
    )
    transaction = LoanTransaction(
        loan_id=loan.id,
        user_id=loan.user_id,
        transaction_type="DISBURSEMENT",
        amount=disbursement_amount,
        principal_amount=disbursement_amount,
        operator_name=operator_name,
        note=note,
    )
    db.add(transaction)
    await db.flush()
    return transaction


def _apply_paid_amount_to_installments(installments: List[LoanInstallment], amount: Any) -> Dict[str, float]:
    remaining = round_money(amount)
    components = {
        "principal_amount": 0.0,
        "interest_amount": 0.0,
        "guarantee_fee_amount": 0.0,
    }

    for item in sorted(installments, key=lambda current: current.period_no):
        if remaining <= 0:
            break

        outstanding_amount = round_money(item.due_amount - item.paid_amount - item.reduction_amount)
        if outstanding_amount <= 0:
            continue

        current_amount = min(remaining, outstanding_amount)
        allocated = split_money_by_weights(
            current_amount,
            {
                "principal_amount": item.principal_amount - item.paid_principal_amount - item.reduced_principal_amount,
                "interest_amount": item.interest_amount - item.paid_interest_amount - item.reduced_interest_amount,
                "guarantee_fee_amount": (
                    item.guarantee_fee_amount
                    - item.paid_guarantee_fee_amount
                    - item.reduced_guarantee_fee_amount
                ),
            },
        )

        item.paid_principal_amount = round_money(item.paid_principal_amount + allocated["principal_amount"])
        item.paid_interest_amount = round_money(item.paid_interest_amount + allocated["interest_amount"])
        item.paid_guarantee_fee_amount = round_money(
            item.paid_guarantee_fee_amount + allocated["guarantee_fee_amount"]
        )
        item.paid_amount = round_money(item.paid_amount + current_amount)

        components["principal_amount"] = round_money(components["principal_amount"] + allocated["principal_amount"])
        components["interest_amount"] = round_money(components["interest_amount"] + allocated["interest_amount"])
        components["guarantee_fee_amount"] = round_money(
            components["guarantee_fee_amount"] + allocated["guarantee_fee_amount"]
        )
        remaining = round_money(remaining - current_amount)

    return components


def _apply_reduction_amount_to_installments(installments: List[LoanInstallment], amount: Any) -> Dict[str, float]:
    remaining = round_money(amount)
    components = {
        "principal_amount": 0.0,
        "interest_amount": 0.0,
        "guarantee_fee_amount": 0.0,
    }

    for item in sorted(installments, key=lambda current: current.period_no):
        if remaining <= 0:
            break

        outstanding_amount = round_money(item.due_amount - item.paid_amount - item.reduction_amount)
        if outstanding_amount <= 0:
            continue

        current_amount = min(remaining, outstanding_amount)
        allocated = split_money_by_weights(
            current_amount,
            {
                "principal_amount": item.principal_amount - item.paid_principal_amount - item.reduced_principal_amount,
                "interest_amount": item.interest_amount - item.paid_interest_amount - item.reduced_interest_amount,
                "guarantee_fee_amount": (
                    item.guarantee_fee_amount
                    - item.paid_guarantee_fee_amount
                    - item.reduced_guarantee_fee_amount
                ),
            },
        )

        item.reduced_principal_amount = round_money(item.reduced_principal_amount + allocated["principal_amount"])
        item.reduced_interest_amount = round_money(item.reduced_interest_amount + allocated["interest_amount"])
        item.reduced_guarantee_fee_amount = round_money(
            item.reduced_guarantee_fee_amount + allocated["guarantee_fee_amount"]
        )
        item.reduction_amount = round_money(item.reduction_amount + current_amount)

        components["principal_amount"] = round_money(components["principal_amount"] + allocated["principal_amount"])
        components["interest_amount"] = round_money(components["interest_amount"] + allocated["interest_amount"])
        components["guarantee_fee_amount"] = round_money(
            components["guarantee_fee_amount"] + allocated["guarantee_fee_amount"]
        )
        remaining = round_money(remaining - current_amount)

    return components


async def register_repayment_async(
    db: AsyncSession,
    loan: Loan,
    amount: Any,
    operator_name: Optional[str] = None,
    note: Optional[str] = None,
    transaction_type: str = "REPAYMENT",
) -> Optional[LoanTransaction]:
    received_amount = round_money(amount)
    if received_amount <= 0:
        return None

    installments = await ensure_installment_records_async(db, loan)
    loan.repaid_amount = round_money(getattr(loan, "repaid_amount", 0) + received_amount)

    penalty_remaining = round_money(getattr(loan, "penalty_amount", 0) - getattr(loan, "paid_penalty_amount", 0) - getattr(loan, "reduced_penalty_amount", 0))
    penalty_amount = min(received_amount, max(penalty_remaining, 0))
    loan.paid_penalty_amount = round_money(getattr(loan, "paid_penalty_amount", 0) + penalty_amount)
    components = _apply_paid_amount_to_installments(installments, round_money(received_amount - penalty_amount))

    transaction = LoanTransaction(
        loan_id=loan.id,
        user_id=loan.user_id,
        transaction_type=transaction_type,
        amount=received_amount,
        principal_amount=components["principal_amount"],
        interest_amount=components["interest_amount"],
        guarantee_fee_amount=components["guarantee_fee_amount"],
        penalty_amount=round_money(penalty_amount),
        operator_name=operator_name,
        note=note,
    )
    db.add(transaction)
    await db.flush()
    sync_loan_repayment_state(loan)
    return transaction


async def register_reduction_async(
    db: AsyncSession,
    loan: Loan,
    amount: Any,
    operator_name: Optional[str] = None,
    note: Optional[str] = None,
    transaction_type: str = "REDUCTION",
) -> Optional[LoanTransaction]:
    reduction_amount = round_money(amount)
    if reduction_amount <= 0:
        return None

    installments = await ensure_installment_records_async(db, loan)
    loan.reduction_amount = round_money(getattr(loan, "reduction_amount", 0) + reduction_amount)

    penalty_remaining = round_money(getattr(loan, "penalty_amount", 0) - getattr(loan, "paid_penalty_amount", 0) - getattr(loan, "reduced_penalty_amount", 0))
    penalty_amount = min(reduction_amount, max(penalty_remaining, 0))
    loan.reduced_penalty_amount = round_money(getattr(loan, "reduced_penalty_amount", 0) + penalty_amount)
    components = _apply_reduction_amount_to_installments(installments, round_money(reduction_amount - penalty_amount))

    transaction = LoanTransaction(
        loan_id=loan.id,
        user_id=loan.user_id,
        transaction_type=transaction_type,
        amount=reduction_amount,
        principal_amount=components["principal_amount"],
        interest_amount=components["interest_amount"],
        guarantee_fee_amount=components["guarantee_fee_amount"],
        penalty_amount=round_money(penalty_amount),
        operator_name=operator_name,
        note=note,
    )
    db.add(transaction)
    await db.flush()
    sync_loan_repayment_state(loan)
    return transaction


async def register_other_fee_async(
    db: AsyncSession,
    loan: Loan,
    amount: Any,
    operator_name: Optional[str] = None,
    note: Optional[str] = None,
    transaction_type: str = "OTHER_FEE",
) -> Optional[LoanTransaction]:
    other_fee_amount = round_money(amount)
    if other_fee_amount <= 0:
        return None

    loan.other_fee_amount = round_money(getattr(loan, "other_fee_amount", 0) + other_fee_amount)
    transaction = LoanTransaction(
        loan_id=loan.id,
        user_id=loan.user_id,
        transaction_type=transaction_type,
        amount=other_fee_amount,
        principal_amount=0.0,
        interest_amount=0.0,
        guarantee_fee_amount=0.0,
        penalty_amount=0.0,
        operator_name=operator_name,
        note=note,
    )
    db.add(transaction)
    await db.flush()
    return transaction
