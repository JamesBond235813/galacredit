import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user_async
from app.api.endpoints.loan import router as loan_router
from app.core.database import get_async_db
from app.models.loan import Loan
from app.models.loan_installment import LoanInstallment
from app.services.loan_flow import get_latest_loan_async


class _ScalarResult:
    def __init__(self, loan):
        self._loan = loan

    def first(self):
        return self._loan


class _ExecuteResult:
    def __init__(self, loan):
        self._loan = loan

    def scalars(self):
        return _ScalarResult(self._loan)


class _FakeAsyncSession:
    def __init__(self, loan):
        self.loan = loan
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _ExecuteResult(self.loan)

    async def commit(self):
        return None

    async def refresh(self, *_args, **_kwargs):
        return None


def _build_loan_with_installments() -> Loan:
    now = datetime.utcnow()
    loan = Loan(
        id=125,
        user_id=1,
        status="DISBURSED",
        credit_limit=1000,
        approved_credit_limit=1000,
        fee_rate=0.6,
        term_days=7,
        due_date=now + timedelta(days=7),
        penalty_amount=0,
        repaid_amount=0,
        reduction_amount=0,
        created_at=now,
    )
    installment = LoanInstallment(
        id=10,
        loan_id=125,
        period_no=1,
        due_date=now + timedelta(days=7),
        status="PENDING",
        principal_amount=1000,
        interest_amount=20,
        guarantee_fee_amount=580,
        due_amount=1600,
        paid_principal_amount=0,
        paid_interest_amount=0,
        paid_guarantee_fee_amount=0,
        paid_amount=0,
        reduced_principal_amount=0,
        reduced_interest_amount=0,
        reduced_guarantee_fee_amount=0,
        reduction_amount=0,
    )
    loan.installments = [installment]
    return loan


def test_get_latest_loan_async_should_eager_load_relations():
    loan = _build_loan_with_installments()
    fake_db = _FakeAsyncSession(loan)

    asyncio.run(get_latest_loan_async(fake_db, user_id=loan.user_id))

    statement = fake_db.statements[0]
    option_paths = [str(item.path) for item in statement._with_options]
    assert any("Loan.installments" in item for item in option_paths)
    assert any("Loan.review_admin" in item for item in option_paths)
    assert any("Loan.collection_admin" in item for item in option_paths)


def test_loan_status_should_return_success_when_installments_exists():
    app = FastAPI()
    app.include_router(loan_router, prefix="/api/loan")
    loan = _build_loan_with_installments()
    fake_db = _FakeAsyncSession(loan)

    async def _override_db():
        yield fake_db

    async def _override_current_user():
        return SimpleNamespace(id=loan.user_id)

    app.dependency_overrides[get_async_db] = _override_db
    app.dependency_overrides[get_current_user_async] = _override_current_user

    client = TestClient(app)
    response = client.get("/api/loan/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == loan.id
    assert payload["fund_flow_summary"]["installment_periods"] == 1
    assert len(payload["installments"]) == 1
