import json
from typing import Any, Dict, List, Optional

from app.services.approved_credit_expiry import APPROVED_CREDIT_VALID_DAYS, get_approved_credit_expires_at


DEFAULT_FEE_RATE = 0.6
LOAN_PERIOD_DAYS = 7
MONTHLY_INTEREST_RATE = 0.02
DEFAULT_UPFRONT_FEE_RATE = 0.4


def round_money(value: Any) -> float:
    return round(float(value or 0), 2)


def normalize_fee_rate(value: Any) -> float:
    if value is None:
        return DEFAULT_FEE_RATE

    rate = max(float(value), 0.0)
    return round(rate, 4)


def calculate_fee_amount(credit_limit: Any, fee_rate: Any) -> float:
    principal = round_money(credit_limit)
    rate = normalize_fee_rate(fee_rate)
    return round_money(principal * rate)


def normalize_installment_ratios(value: Any, installment_count: Any = 1) -> List[float]:
    """规范化分期比例，并将空配置转换为等比例分期。

    :param value: JSON、列表或逗号分隔的比例值
    :param installment_count: 分期期数
    :return: 和为1的比例列表
    """
    try:
        count = max(int(installment_count or 1), 1)
    except (TypeError, ValueError):
        count = 1
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value)
        except (TypeError, ValueError):
            raw = [item.strip() for item in value.split(",") if item.strip()]
    if not isinstance(raw, (list, tuple)) or len(raw) != count:
        return [round(1 / count, 8)] * count
    numbers = [max(float(item or 0), 0) for item in raw]
    total = sum(numbers)
    if total <= 0:
        return [round(1 / count, 8)] * count
    return [round(item / total, 8) for item in numbers]


def calculate_cash_loan_amounts(nominal_amount: Any, upfront_fee_rate: Any) -> Dict[str, float]:
    """计算加纳现金贷的名义金额、上扣费用和实际到账金额。

    :param nominal_amount: 用户名义借款额，也是正常总应还金额
    :param upfront_fee_rate: 上扣费用率，例如40%传入0.4
    :return: 金额快照字典
    """
    nominal = round_money(nominal_amount)
    rate = max(float(upfront_fee_rate or 0), 0)
    fee = round_money(nominal * rate)
    return {
        "nominal_loan_amount": nominal,
        "upfront_fee_amount": fee,
        "actual_disbursement_amount": round_money(max(nominal - fee, 0)),
        "total_repayment_amount": nominal,
    }


def calculate_installment_amounts(total_amount: Any, ratios: Any, installment_count: Any = 1) -> List[float]:
    """按后台配置比例拆分总应还金额，并把分币误差放入最后一期。

    :param total_amount: 总应还金额
    :param ratios: 每期比例配置
    :param installment_count: 分期期数
    :return: 每期应还金额列表
    """
    normalized = normalize_installment_ratios(ratios, installment_count)
    total_cents = int(round(float(total_amount or 0) * 100))
    amounts = [int(total_cents * ratio) for ratio in normalized]
    amounts[-1] += total_cents - sum(amounts)
    return [round_money(item / 100) for item in amounts]


def calculate_interest_amount(credit_limit: Any, term_days: Any) -> float:
    principal = round_money(credit_limit)
    if not principal or term_days in (None, ""):
        return 0.0

    try:
        normalized_term_days = normalize_term_days(term_days)
    except ValueError:
        return 0.0

    return round_money(principal * MONTHLY_INTEREST_RATE * normalized_term_days / 30)


def calculate_guarantee_fee_amount(total_fee_amount: Any, credit_limit: Any, term_days: Any) -> float:
    total_fee = round_money(total_fee_amount)
    interest_amount = calculate_interest_amount(credit_limit, term_days)
    return round_money(max(total_fee - interest_amount, 0.0))


def calculate_total_repayment_by_values(
    credit_limit: Any,
    fee_rate: Any,
    penalty_amount: Any = 0,
) -> float:
    principal = round_money(credit_limit)
    fee_amount = calculate_fee_amount(principal, fee_rate)
    penalty = round_money(penalty_amount)
    return round_money(principal + fee_amount + penalty)


def normalize_term_days(term_days: Any, allow_empty: bool = False) -> Optional[int]:
    if term_days in (None, ""):
        if allow_empty:
            return None
        raise ValueError("请填写账期天数")

    try:
        numeric_term = float(term_days)
    except (TypeError, ValueError) as exc:
        raise ValueError("账期格式不正确") from exc

    if not numeric_term.is_integer():
        raise ValueError("期限必须为整数天")

    term = int(numeric_term)
    if term < 1:
        raise ValueError("期限不能少于1天")
    return term


def calculate_installment_periods(term_days: Any) -> int:
    normalize_term_days(term_days)
    return 1


def calculate_installment_by_values(
    credit_limit: Any,
    fee_rate: Any,
    term_days: Any,
) -> float:
    if not term_days:
        return 0.0

    try:
        periods = calculate_installment_periods(term_days)
    except (TypeError, ValueError):
        return 0.0

    principal = round_money(credit_limit)
    total_without_penalty = round_money(principal + calculate_fee_amount(principal, fee_rate))
    return round_money(total_without_penalty / periods)


def calculate_total_repayment_amount(loan: Any) -> float:
    snapshot_total = round_money(getattr(loan, "total_repayment_amount_snapshot", 0))
    if snapshot_total > 0:
        return round_money(snapshot_total + getattr(loan, "penalty_amount", 0))
    return calculate_total_repayment_by_values(
        getattr(loan, "credit_limit", 0),
        getattr(loan, "fee_rate", DEFAULT_FEE_RATE),
        getattr(loan, "penalty_amount", 0),
    )


def calculate_installment_amount(loan: Any) -> float:
    snapshot_total = round_money(getattr(loan, "total_repayment_amount_snapshot", 0))
    if snapshot_total > 0:
        amounts = calculate_installment_amounts(
            snapshot_total,
            getattr(loan, "installment_ratios_json", None),
            getattr(loan, "installment_count", 1),
        )
        return amounts[0] if amounts else 0.0
    return calculate_installment_by_values(
        getattr(loan, "credit_limit", 0),
        getattr(loan, "fee_rate", DEFAULT_FEE_RATE),
        getattr(loan, "term_days", None),
    )


def calculate_remaining_repayment_amount(loan: Any) -> float:
    total_amount = calculate_total_repayment_amount(loan)
    paid_and_reduced = round_money(getattr(loan, "repaid_amount", 0)) + round_money(
        getattr(loan, "reduction_amount", 0)
    )
    return round_money(max(total_amount - paid_and_reduced, 0.0))


def mask_secret(value: Any, left: int = 3, right: int = 2) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) <= left + right:
        return "*" * len(text)
    return f"{text[:left]}{'*' * (len(text) - left - right)}{text[-right:]}"


def serialize_loan_ecard_item(item: Any, index: int = 0) -> dict:
    """序列化订单E卡明细。

    :param item: 订单E卡明细对象
    :param index: 明细序号
    :return: 脱敏后的E卡明细
    """
    return {
        "id": getattr(item, "id", None),
        "ecard_pool_id": getattr(item, "ecard_pool_id", None),
        "index": index,
        "face_value": round_money(getattr(item, "face_value", 0)),
        "account_masked": mask_secret(getattr(item, "account", None), left=4, right=4) or None,
        "password_masked": mask_secret(getattr(item, "password", None), left=4, right=4) or None,
        "expires_at": getattr(item, "expires_at", None),
    }


def get_serialized_loan_ecard_items(loan: Any) -> list[dict]:
    """获取订单E卡明细，兼容历史单卡字段。

    :param loan: 订单对象
    :return: 订单E卡明细列表
    """
    loaded_items = getattr(loan, "__dict__", {}).get("ecard_items")
    if loaded_items:
        return [
            serialize_loan_ecard_item(item, index=index)
            for index, item in enumerate(loaded_items)
            if getattr(item, "account", None) and getattr(item, "password", None)
        ]

    if getattr(loan, "ecard_account", None) and getattr(loan, "ecard_password", None):
        legacy_item = type(
            "LegacyLoanEcard",
            (),
            {
                "id": None,
                "ecard_pool_id": None,
                "face_value": getattr(loan, "ecard_face_value", 0),
                "account": getattr(loan, "ecard_account", None),
                "password": getattr(loan, "ecard_password", None),
                "expires_at": getattr(loan, "ecard_expires_at", None),
            },
        )()
        return [serialize_loan_ecard_item(legacy_item, index=0)]

    return []


def sync_loan_fee_fields(loan: Any, fee_rate: Any = None):
    normalized_rate = normalize_fee_rate(
        fee_rate if fee_rate is not None else getattr(loan, "fee_rate", DEFAULT_FEE_RATE)
    )
    loan.fee_rate = normalized_rate
    loan.fee_amount = calculate_fee_amount(getattr(loan, "credit_limit", 0), normalized_rate)
    return loan


def serialize_loan_snapshot(loan: Any, include_user: bool = False, include_ledger: bool = False):
    credit_limit = getattr(loan, "credit_limit", 0)
    term_days = getattr(loan, "term_days", None)
    fee_rate = normalize_fee_rate(getattr(loan, "fee_rate", DEFAULT_FEE_RATE))
    fee_amount = calculate_fee_amount(credit_limit, fee_rate)
    interest_amount = calculate_interest_amount(credit_limit, term_days)
    guarantee_fee_amount = calculate_guarantee_fee_amount(fee_amount, credit_limit, term_days)

    review_admin = getattr(loan, "__dict__", {}).get("review_admin")
    collection_admin = getattr(loan, "__dict__", {}).get("collection_admin")
    ecard_items = get_serialized_loan_ecard_items(loan)

    payload = {
        "id": loan.id,
        "user_id": loan.user_id,
        "status": loan.status,
        "credit_limit": round_money(credit_limit),
        "approved_credit_limit": round_money(getattr(loan, "approved_credit_limit", 0) or credit_limit),
        "term_days": term_days,
        "due_date": getattr(loan, "due_date", None),
        "fee_rate": fee_rate,
        "fee_amount": fee_amount,
        "nominal_loan_amount": round_money(getattr(loan, "nominal_loan_amount", 0) or credit_limit),
        "upfront_fee_amount": round_money(getattr(loan, "upfront_fee_amount", 0) or fee_amount),
        "actual_disbursement_amount": round_money(
            getattr(loan, "actual_disbursement_amount", 0)
            or max(round_money(getattr(loan, "nominal_loan_amount", 0) or credit_limit) - fee_amount, 0)
        ),
        "interest_start_day": int(getattr(loan, "interest_start_day", 1) or 1),
        "repayment_due_day": int(getattr(loan, "repayment_due_day", 7) or 7),
        "installment_count": int(getattr(loan, "installment_count", 1) or 1),
        "momo_disbursement_reference": getattr(loan, "momo_disbursement_reference", None),
        "interest_amount": interest_amount,
        "guarantee_fee_amount": guarantee_fee_amount,
        "installment_amount": calculate_installment_by_values(
            credit_limit,
            fee_rate,
            term_days,
        ),
        "penalty_amount": round_money(getattr(loan, "penalty_amount", 0)),
        "paid_penalty_amount": round_money(getattr(loan, "paid_penalty_amount", 0)),
        "reduced_penalty_amount": round_money(getattr(loan, "reduced_penalty_amount", 0)),
        "repaid_amount": round_money(getattr(loan, "repaid_amount", 0)),
        "reduction_amount": round_money(getattr(loan, "reduction_amount", 0)),
        "other_fee_amount": round_money(getattr(loan, "other_fee_amount", 0)),
        "actual_repayment_date": getattr(loan, "actual_repayment_date", None),
        "total_repayment_amount": calculate_total_repayment_by_values(
            credit_limit,
            fee_rate,
            getattr(loan, "penalty_amount", 0),
        ),
        "remaining_repayment_amount": calculate_remaining_repayment_amount(loan),
        "review_note": getattr(loan, "review_note", None),
        "approved_at": getattr(loan, "approved_at", None),
        "approved_credit_valid_days": APPROVED_CREDIT_VALID_DAYS,
        "approved_credit_expires_at": get_approved_credit_expires_at(loan),
        "reminder_count": getattr(loan, "reminder_count", 0) or 0,
        "last_reminded_at": getattr(loan, "last_reminded_at", None),
        "collection_count": getattr(loan, "collection_count", 0) or 0,
        "last_collection_at": getattr(loan, "last_collection_at", None),
        "collection_note": getattr(loan, "collection_note", None),
        "risk_report_checked_at": getattr(loan, "risk_report_checked_at", None),
        "risk_report_checked_by": getattr(loan, "risk_report_checked_by", None),
        "approval_discount_amount": round_money(getattr(loan, "approval_discount_amount", 0)),
        "order_discount_amount": round_money(getattr(loan, "order_discount_amount", 0)),
        "card_reissue_closed": bool(getattr(loan, "card_reissue_closed", False)),
        "extension_count": int(getattr(loan, "extension_count", 0) or 0),
        "extension_type": getattr(loan, "extension_type", None),
        "extension_note": getattr(loan, "extension_note", None),
        "overdue_hidden": bool(getattr(loan, "overdue_hidden", False)),
        "available_credit_limit": round_money(getattr(getattr(loan, "owner", None), "available_credit_limit", 0)),
        "overdue_credit_locked": bool(getattr(getattr(loan, "owner", None), "overdue_credit_locked", False)),
        "extension_source_loan_id": getattr(loan, "extension_source_loan_id", None),
        "extension_used_at": getattr(loan, "extension_used_at", None),
        "is_extension_fee_order": bool(getattr(loan, "is_extension_fee_order", False)),
        "identity_ocr_submitted_at": getattr(loan, "identity_ocr_submitted_at", None),
        "identity_face_auth_at": getattr(loan, "identity_face_auth_at", None),
        "fee_extension_ready": bool(getattr(loan, "fee_extension_ready", False)),
        "review_admin_id": getattr(loan, "review_admin_id", None),
        "review_admin_name": getattr(review_admin, "username", None),
        "collection_admin_id": getattr(loan, "collection_admin_id", None),
        "collection_admin_name": getattr(collection_admin, "username", None),
        "collection_transferred_at": getattr(loan, "collection_transferred_at", None),
        "repay_attempt_count": int(getattr(loan, "repay_attempt_count", 0) or 0),
        "product_id": getattr(loan, "product_id", None),
        "product_type": getattr(loan, "product_type", None),
        "product_name": getattr(loan, "product_name", None),
        "rights_title": getattr(loan, "rights_title", None),
        "rights_desc": getattr(loan, "rights_desc", None),
        "rights_contact_phone": getattr(loan, "rights_contact_phone", None),
        "rights_price": round_money(getattr(loan, "rights_price", 0)),
        "ecard_face_value": round_money(getattr(loan, "ecard_face_value", 0)),
        "product_total_price": round_money(
            getattr(loan, "product_total_price", 0)
            or round_money(
                round_money(getattr(loan, "ecard_face_value", 0) or credit_limit)
                + round_money(getattr(loan, "rights_price", 0) or fee_amount)
            )
        ),
        "product_term_days": getattr(loan, "product_term_days", None) or term_days,
        "ecard_account_masked": mask_secret(getattr(loan, "ecard_account", None), left=4, right=4) or None,
        "ecard_password_masked": mask_secret(getattr(loan, "ecard_password", None), left=4, right=4) or None,
        "ecard_expires_at": getattr(loan, "ecard_expires_at", None),
        "ecard_items": ecard_items,
        "has_issued_ecard": bool(ecard_items),
        "relend_count": int(getattr(loan, "relend_count", 0) or 0),
        "relend_label": getattr(loan, "relend_label", None) or "首购",
        "created_at": getattr(loan, "created_at", None),
        "disbursed_at": getattr(loan, "disbursed_at", None),
    }

    latest_settled_loan = getattr(loan, "__dict__", {}).get("latest_settled_loan")
    if latest_settled_loan is not None:
        payload["latest_settled_loan"] = serialize_loan_snapshot(latest_settled_loan)

    if include_ledger:
        from app.services.loan_ledger import get_loan_ledger_snapshot

        ledger = get_loan_ledger_snapshot(loan)
        payload["installment_periods"] = ledger["summary"]["installment_periods"]
        payload["installments"] = ledger["installments"]
        payload["fund_flow_summary"] = ledger["summary"]

    if include_user:
        from app.services.upload_storage import build_upload_url

        owner = getattr(loan, "__dict__", {}).get("owner")
        source_channel = getattr(owner, "__dict__", {}).get("source_channel") if owner else None
        payload.update(
            {
                "user_phone": owner.phone if owner else "",
                "user_name": owner.name if owner else None,
                "user_id_card_num": owner.id_card_num if owner else None,
                "id_card_front_image_url": build_upload_url(getattr(owner, "id_card_front_image", None)) if owner else None,
                "id_card_back_image_url": build_upload_url(getattr(owner, "id_card_back_image", None)) if owner else None,
                "face_image_url": build_upload_url(getattr(owner, "face_image", None)) if owner else None,
                "user_face_auth_status": owner.face_auth_status if owner else None,
                "user_real_name_status": owner.real_name_status if owner else None,
                "user_blacklist_hit": bool(getattr(owner, "blacklist_hit", False)) if owner else False,
                "user_blacklist_reason": getattr(owner, "blacklist_reason", None) if owner else None,
                "user_risk_list_hit": bool(getattr(owner, "risk_list_hit", False)) if owner else False,
                "user_risk_list_source": getattr(owner, "risk_list_source", None) if owner else None,
                "user_risk_list_reason": getattr(owner, "risk_list_reason", None) if owner else None,
                "user_risk_list_checked_at": getattr(owner, "risk_list_checked_at", None) if owner else None,
                "user_source_channel_name": source_channel.channel_name if source_channel else None,
                "user_source_channel_sales_name": source_channel.sales_name if source_channel else None,
                "application_submitted_at": owner.application_submitted_at if owner else None,
                "last_login_at": owner.last_login_at if owner else None,
            }
        )

    return payload
