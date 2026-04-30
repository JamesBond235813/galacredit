import pytest

from app.models.loan import Loan
from app.services.loan_flow import create_init_loan_async


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def first(self):
        return self._value


class _ExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return _ScalarResult(self._value)


class _FakeDb:
    def __init__(self, latest_loan=None):
        self.latest_loan = latest_loan
        self.added = []
        self.flush_called = False

    async def execute(self, statement):
        sql_text = str(statement)
        if "FROM users" in sql_text:
            return _ExecuteResult(None)
        if "FROM loans" in sql_text:
            return _ExecuteResult(self.latest_loan)
        return _ExecuteResult(None)

    def add(self, obj):
        obj.id = 1001
        self.added.append(obj)

    async def flush(self):
        self.flush_called = True


@pytest.mark.asyncio
async def test_create_init_loan_should_reuse_latest_active_loan():
    active = Loan(id=88, user_id=124, status="REVIEWING")
    db = _FakeDb(latest_loan=active)

    loan = await create_init_loan_async(db, 124)

    assert loan.id == 88
    assert loan.status == "REVIEWING"
    assert db.added == []
    assert db.flush_called is False


@pytest.mark.asyncio
async def test_create_init_loan_should_create_when_latest_settled():
    settled = Loan(id=77, user_id=124, status="SETTLED")
    db = _FakeDb(latest_loan=settled)

    loan = await create_init_loan_async(db, 124)

    assert loan.status == "INIT"
    assert len(db.added) == 1
    assert db.flush_called is True
