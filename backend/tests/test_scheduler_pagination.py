import asyncio
from datetime import datetime
from types import SimpleNamespace

from app.services import scheduler


def test_process_overdue_loans_should_scan_loans_by_id_with_page_size_200(monkeypatch):
    loans = [
        SimpleNamespace(
            id=i,
            status="DISBURSED",
            due_date=datetime(2026, 1, 1),
            owner=None,
            penalty_amount=0.0,
        )
        for i in range(1, 451)
    ]
    execute_page_sizes = []

    class _ScalarResult:
        def __init__(self, items):
            self._items = items

        def all(self):
            return self._items

    class _ExecuteResult:
        def __init__(self, items):
            self._items = items

        def scalars(self):
            return _ScalarResult(self._items)

    class _FakeDb:
        def __init__(self):
            self._last_id = 0
            self.committed = False

        async def execute(self, _stmt):
            page = [item for item in loans if item.id > self._last_id][:scheduler.LOAN_SCAN_PAGE_SIZE]
            execute_page_sizes.append(len(page))
            if page:
                self._last_id = page[-1].id
            return _ExecuteResult(page)

        async def commit(self):
            self.committed = True

    class _FakeSessionCtx:
        def __init__(self, db):
            self.db = db

        async def __aenter__(self):
            return self.db

        async def __aexit__(self, exc_type, exc, tb):
            return False

    db = _FakeDb()
    async def _fake_ensure_installments(*_args, **_kwargs):
        return []

    async def _fake_assign_collection(*_args, **_kwargs):
        return None

    monkeypatch.setattr(scheduler, "AsyncSessionLocal", lambda: _FakeSessionCtx(db))
    monkeypatch.setattr(scheduler, "ensure_installment_records_async", _fake_ensure_installments)
    monkeypatch.setattr(scheduler, "sync_loan_repayment_state", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(scheduler, "assign_collection_admins_for_overdue_loans_async", _fake_assign_collection)

    asyncio.run(scheduler.process_overdue_loans())

    assert execute_page_sizes == [200, 200, 50, 0]
    assert db.committed is True
