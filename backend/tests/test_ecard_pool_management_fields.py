import asyncio
from datetime import datetime
from types import SimpleNamespace

from app.api.endpoints import loan as loan_endpoint
from app.services import admin_service


def test_ecard_pool_serializer_should_include_recipient_and_copy_time():
    copied_at = datetime(2026, 5, 26, 10, 30, 0)
    item = SimpleNamespace(
        id=7,
        account="1234567890",
        password="abcdef",
        face_value=1000,
        expires_at=datetime(2026, 6, 1),
        status="ASSIGNED",
        loan_id=88,
        recipient_phone="15805655619",
        secret_copied_at=copied_at,
        note="",
        assigned_at=datetime(2026, 5, 26, 9, 0, 0),
        created_at=datetime(2026, 5, 25, 9, 0, 0),
        updated_at=datetime(2026, 5, 26, 9, 0, 0),
    )

    result = admin_service.serialize_ecard_pool_item(item)

    assert result["recipient_phone"] == "15805655619"
    assert result["secret_copied_at"] == copied_at
    assert result["assigned_at"] == item.assigned_at


def test_copy_detail_parser_should_extract_ecard_pool_id():
    detail = "field=password；loan_ecard_id=39；ecard_pool_id=15；index=0"

    assert admin_service._extract_ecard_pool_id_from_copy_detail(detail) == 15
    assert admin_service._extract_ecard_pool_id_from_copy_detail("field=account") is None


def test_record_ecard_secret_copy_should_write_password_event_detail(monkeypatch):
    async def _run():
        events = []

        async def fake_log_user_event_async(db, **kwargs):
            events.append(kwargs)

        class FakeDb:
            def __init__(self):
                self.committed = False

            async def commit(self):
                self.committed = True

        fake_db = FakeDb()
        monkeypatch.setattr(loan_endpoint, "log_user_event_async", fake_log_user_event_async)

        await loan_endpoint._record_ecard_secret_copy(
            fake_db,
            user=SimpleNamespace(id=1),
            loan=SimpleNamespace(id=2),
            field="password",
            loan_ecard_id=39,
            ecard_pool_id=15,
            index=0,
        )

        assert fake_db.committed is True
        assert events[0]["event_type"] == "USER_ECARD_SECRET_COPIED"
        assert events[0]["detail"] == "field=password；loan_ecard_id=39；ecard_pool_id=15；index=0"

    asyncio.run(_run())


def test_ecard_pool_stats_should_count_total_today_stock_in_and_today_assigned(monkeypatch):
    async def _run():
        class ExecuteResult:
            def __init__(self, row):
                self.row = row

            def one(self):
                return self.row

        class FakeDb:
            def __init__(self):
                self.rows = [(10, 8500), (6, 6000), (4, 3500), (2, 1500), (3, 2500)]

            async def execute(self, _stmt):
                return ExecuteResult(self.rows.pop(0))

        stats = await admin_service._build_ecard_pool_stats(FakeDb())

        assert stats == {
            "pool_total_count": 10,
            "pool_total_amount": 8500.0,
            "cumulative_assigned_count": 6,
            "cumulative_assigned_amount": 6000.0,
            "available_count": 4,
            "available_amount": 3500.0,
            "today_stock_in_count": 2,
            "today_stock_in_amount": 1500.0,
            "today_assigned_count": 3,
            "today_assigned_amount": 2500.0,
        }

    asyncio.run(_run())
