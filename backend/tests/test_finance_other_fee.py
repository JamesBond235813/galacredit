from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.schemas.loan import LoanFinanceReconcileRequest
from app.services import admin_service
from app.services.admin_service import build_project_cash_insights, split_extra_fee_for_penalty
from app.services.loan_amounts import calculate_remaining_repayment_amount
from app.services.loan_ledger import register_other_fee_async


class _FakeDb:
    def __init__(self):
        self.added = []
        self.scalar_values = [12, 3, 2, 400, 100]

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        return None

    async def scalar(self, _stmt):
        return self.scalar_values.pop(0)


@pytest.mark.asyncio
async def test_register_other_fee_should_not_change_remaining_repayment_amount():
    db = _FakeDb()
    loan = SimpleNamespace(
        id=18,
        user_id=201,
        credit_limit=1000,
        fee_rate=0.6,
        penalty_amount=0,
        repaid_amount=0,
        reduction_amount=0,
        other_fee_amount=0,
    )

    transaction = await register_other_fee_async(db, loan, 100, operator_name="finance01", note="补收其他费用")

    assert transaction is not None
    assert transaction.transaction_type == "OTHER_FEE"
    assert transaction.amount == 100
    assert loan.other_fee_amount == 100
    assert calculate_remaining_repayment_amount(loan) == 1600


@pytest.mark.asyncio
async def test_project_cash_insights_should_include_other_fee_card():
    db = _FakeDb()
    today_start = datetime(2026, 5, 24, 0, 0, 0)
    tomorrow = datetime(2026, 5, 25, 0, 0, 0)
    loans = [
        SimpleNamespace(
            user_id=1,
            status="DISBURSED",
            credit_limit=1000,
            ecard_face_value=1000,
            fee_rate=0.6,
            penalty_amount=0,
            repaid_amount=1600,
            reduction_amount=0,
            other_fee_amount=100,
            rights_price=600,
            disbursed_at=today_start,
            due_date=tomorrow,
        ),
        SimpleNamespace(
            user_id=2,
            status="OVERDUE",
            credit_limit=1000,
            ecard_face_value=1000,
            fee_rate=0.6,
            penalty_amount=0,
            repaid_amount=0,
            reduction_amount=0,
            other_fee_amount=50,
            rights_price=600,
            disbursed_at=today_start,
            due_date=today_start,
        ),
    ]

    payload = await build_project_cash_insights(db, loans, today_start, tomorrow)

    other_fee_card = next(item for item in payload["cards"] if item["key"] == "other_fee_amount")
    assert other_fee_card["value"] == 150
    assert other_fee_card["sub_value"] == 100
    assert payload["total_other_fee_amount"] == 150
    assert payload["total_net_amount"] == -298


def test_split_extra_fee_for_penalty_should_pay_penalty_first():
    result = split_extra_fee_for_penalty(100, 20)

    assert result == {
        "penalty_paid_now": 20,
        "other_fee_amount": 80,
    }


class _FakeScalarResult:
    def __init__(self, loan):
        self._loan = loan

    def scalar_one_or_none(self):
        return self._loan


class _FakeFinanceDb:
    def __init__(self, loan):
        self._loan = loan
        self.committed = False
        self.refreshed = False

    async def execute(self, _stmt):
        return _FakeScalarResult(self._loan)

    async def commit(self):
        self.committed = True

    async def refresh(self, _loan):
        self.refreshed = True


@pytest.mark.asyncio
async def test_finance_reconcile_should_freeze_penalty_by_actual_repayment_date_and_split_extra_fee(
    monkeypatch,
):
    owner = SimpleNamespace(available_credit_limit=0, overdue_credit_locked=False)
    loan = SimpleNamespace(
        id=88,
        user_id=501,
        status="OVERDUE",
        owner=owner,
        due_date=datetime(2026, 5, 21, 10, 0, 0),
        credit_limit=1000,
        fee_rate=0.6,
        penalty_amount=0,
        paid_penalty_amount=0,
        reduced_penalty_amount=0,
        repaid_amount=0,
        reduction_amount=0,
        other_fee_amount=0,
        actual_repayment_date=None,
        installments=[],
    )
    db = _FakeFinanceDb(loan)
    current_admin = SimpleNamespace(id=1, username="finance01", roles='["ADMIN"]')
    event_log = {}

    monkeypatch.setattr(admin_service, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)

    async def _fake_penalty(_db, _due_date, actual_repayment_date):
        assert actual_repayment_date == date(2026, 5, 23)
        return {
            "penalty_amount": 20,
            "overdue_days": 2,
            "daily_penalty_amount": 10,
        }

    async def _fake_installments(_db, _loan):
        return []

    async def _fake_register_repayment(_db, target_loan, amount, **_kwargs):
        target_loan.repaid_amount += amount
        penalty_amount = min(
            amount,
            max(target_loan.penalty_amount - target_loan.paid_penalty_amount - target_loan.reduced_penalty_amount, 0),
        )
        target_loan.paid_penalty_amount += penalty_amount
        return SimpleNamespace(amount=amount, penalty_amount=penalty_amount)

    async def _fake_register_reduction(_db, target_loan, amount, **_kwargs):
        target_loan.reduction_amount += amount
        return SimpleNamespace(amount=amount)

    async def _fake_register_other_fee(_db, target_loan, amount, **_kwargs):
        target_loan.other_fee_amount += amount
        return SimpleNamespace(amount=amount)

    async def _fake_log_user_event_async(_db, **kwargs):
        event_log.update(kwargs)

    monkeypatch.setattr(admin_service, "calculate_penalty_by_repayment_date", _fake_penalty)
    monkeypatch.setattr(admin_service, "ensure_installment_records_async", _fake_installments)
    monkeypatch.setattr(admin_service, "register_repayment_async", _fake_register_repayment)
    monkeypatch.setattr(admin_service, "register_reduction_async", _fake_register_reduction)
    monkeypatch.setattr(admin_service, "register_other_fee_async", _fake_register_other_fee)
    monkeypatch.setattr(admin_service, "sync_loan_repayment_state", lambda target_loan: setattr(
        target_loan,
        "status",
        "SETTLED" if calculate_remaining_repayment_amount(target_loan) <= 0 else target_loan.status,
    ))
    monkeypatch.setattr(admin_service, "serialize_loan", lambda target_loan: {
        "id": target_loan.id,
        "status": target_loan.status,
        "repaid_amount": target_loan.repaid_amount,
        "other_fee_amount": target_loan.other_fee_amount,
        "paid_penalty_amount": target_loan.paid_penalty_amount,
        "actual_repayment_date": target_loan.actual_repayment_date,
    })
    monkeypatch.setattr(admin_service, "log_user_event_async", _fake_log_user_event_async)

    result = await admin_service._finance_reconcile_loan(
        db=db,
        current_admin=current_admin,
        loan_id=loan.id,
        req=LoanFinanceReconcileRequest(
            received_amount=1600,
            reduction_amount=0,
            other_fee_amount=100,
            actual_repayment_date=date(2026, 5, 23),
            note="冷军补录",
        ),
    )

    assert loan.penalty_amount == 20
    assert loan.actual_repayment_date == date(2026, 5, 23)
    assert loan.paid_penalty_amount == 20
    assert loan.repaid_amount == 1620
    assert loan.other_fee_amount == 80
    assert calculate_remaining_repayment_amount(loan) == 0
    assert loan.status == "SETTLED"
    assert db.committed is True
    assert db.refreshed is True
    assert result["other_fee_amount"] == 80
    assert "额外收款冲抵逾期费 20.00 元" in event_log["detail"]
    assert "登记其他费用 80.00 元" in event_log["detail"]
