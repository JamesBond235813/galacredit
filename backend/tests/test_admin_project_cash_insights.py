import asyncio
from types import SimpleNamespace

from sqlalchemy.exc import InvalidRequestError

from app.api.endpoints import admin as admin_endpoints


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows
        self._unique_called = False

    def unique(self):
        self._unique_called = True
        return self

    def scalars(self):
        return self

    def all(self):
        if not self._unique_called:
            raise InvalidRequestError("The unique() method must be invoked on this Result")
        return self._rows


class _FakeAsyncSession:
    def __init__(self, rows):
        self._result = _FakeResult(rows)

    async def execute(self, _stmt):
        return self._result


def test_project_cash_insights_should_call_unique_before_scalars_all(monkeypatch):
    fake_loans = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    fake_db = _FakeAsyncSession(fake_loans)
    fake_admin = SimpleNamespace(permissions='["overview"]', roles='[]')

    async def _fake_build_project_cash_insights(_db, loans, _today_start, _tomorrow):
        return {"loan_count": len(loans)}

    monkeypatch.setattr(admin_endpoints, "build_project_cash_insights", _fake_build_project_cash_insights)

    result = asyncio.run(admin_endpoints.get_project_cash_insights(db=fake_db, current_admin=fake_admin))

    assert result == {"loan_count": 2}
