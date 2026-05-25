from types import SimpleNamespace
from datetime import datetime

import pytest

from app.api.endpoints import admin


class _FakeLoanRows:
    def __init__(self, rows):
        self._rows = rows

    def unique(self):
        return self

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeDb:
    def __init__(self, loans):
        self._loans = loans
        self.loan_stmt_sql = ""
        self.total_stmt_sql = ""

    async def scalar(self, stmt):
        self.total_stmt_sql = str(stmt)
        return len(self._loans)

    async def execute(self, stmt):
        self.loan_stmt_sql = str(stmt)
        return _FakeLoanRows(self._loans)


@pytest.mark.asyncio
async def test_get_loans_should_build_reviewer_and_relend_filters(monkeypatch):
    monkeypatch.setattr(admin, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin, "ensure_any_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin, "serialize_loan", lambda loan: {"id": loan.id})

    loan = SimpleNamespace(id=11)
    db = _FakeDb([loan])
    current_admin = SimpleNamespace(id=1, username="root", roles='["ADMIN"]')

    result = await admin.get_loans(
        status="REVIEWING",
        phone=None,
        scope="REVIEWING",
        due_date_preset=None,
        actual_repayment_start=None,
        actual_repayment_end=None,
        review_admin_id=7,
        relend_count=2,
        relend_min_count=None,
        overdue_min_days=None,
        overdue_max_days=None,
        skip=0,
        limit=20,
        db=db,
        current_admin=current_admin,
    )

    assert result["items"] == [{"id": 11}]
    combined_sql = f"{db.total_stmt_sql}\n{db.loan_stmt_sql}"
    assert "review_admin_id" in combined_sql
    assert "count(loans_1.id)" in combined_sql
    assert "loans_1.status" in combined_sql
    assert "loans_1.id < loans.id" in combined_sql


@pytest.mark.asyncio
async def test_repayment_stats_should_follow_due_date_preset(monkeypatch):
    monkeypatch.setattr(admin, "ensure_any_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin, "get_today_range", lambda: (datetime(2026, 5, 22), datetime(2026, 5, 23)))
    monkeypatch.setattr(admin, "get_loan_operating_metrics", lambda _loan: {
        "expected_interest_amount": 0,
        "expected_guarantee_fee_amount": 0,
        "expected_income_amount": 0,
        "realized_income_amount": 0,
        "principal_balance_amount": 0,
        "reduced_principal_amount": 0,
        "reduced_fee_amount": 0,
        "remaining_amount": 0,
    })

    loans = [
        SimpleNamespace(
            id=1,
            user_id=1,
            status="DISBURSED",
            credit_limit=100,
            fee_rate=0,
            penalty_amount=0,
            repaid_amount=25,
            reduction_amount=0,
            other_fee_amount=0,
        ),
        SimpleNamespace(
            id=2,
            user_id=2,
            status="SETTLED",
            credit_limit=300,
            fee_rate=0,
            penalty_amount=0,
            repaid_amount=75,
            reduction_amount=10,
            other_fee_amount=0,
        ),
    ]
    db = _FakeDb(loans)
    current_admin = SimpleNamespace(id=1, username="root", roles='["ADMIN"]')

    result = await admin.get_repayment_stats(
        due_date_preset="TODAY",
        actual_repayment_start=None,
        actual_repayment_end=None,
        db=db,
        current_admin=current_admin,
    )

    assert result["receivable_order_count"] == 2
    assert result["receivable_amount"] == 400
    assert result["received_amount"] == 100
    assert result["repayment_rate"] == 25
    assert "loans.due_date" in db.loan_stmt_sql


@pytest.mark.asyncio
async def test_get_loans_should_apply_actual_repayment_date_range(monkeypatch):
    monkeypatch.setattr(admin, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin, "ensure_any_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin, "serialize_loan", lambda loan: {"id": loan.id})

    loan = SimpleNamespace(id=12)
    db = _FakeDb([loan])
    current_admin = SimpleNamespace(id=1, username="root", roles='["ADMIN"]')

    result = await admin.get_loans(
        status=None,
        phone=None,
        scope="REPAYMENTS",
        due_date_preset=None,
        actual_repayment_start=datetime(2026, 5, 20).date(),
        actual_repayment_end=datetime(2026, 5, 24).date(),
        review_admin_id=None,
        relend_count=None,
        relend_min_count=None,
        overdue_min_days=None,
        overdue_max_days=None,
        skip=0,
        limit=20,
        db=db,
        current_admin=current_admin,
    )

    assert result["items"] == [{"id": 12}]
    combined_sql = f"{db.total_stmt_sql}\n{db.loan_stmt_sql}"
    assert "actual_repayment_date" in combined_sql
