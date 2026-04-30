import pytest

from app.schemas.admin import RegisterUserRequest
from app.services import admin_service


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDb:
    def __init__(self):
        self.added = []
        self.flushed = False
        self.committed = False

    async def execute(self, _stmt):
        return _ScalarResult(None)

    def add(self, obj):
        obj.id = 101
        self.added.append(obj)

    async def flush(self):
        self.flushed = True

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_register_user_should_allow_missing_source_channel(monkeypatch):
    async def _noop_log(*_args, **_kwargs):
        return None

    monkeypatch.setattr(admin_service, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin_service, "log_user_event_async", _noop_log)
    monkeypatch.setattr(admin_service, "get_password_hash", lambda value: f"hashed:{value}")

    db = _FakeDb()
    current_admin = type("Admin", (), {"username": "tester"})()
    req = RegisterUserRequest(phone="13800000000", password="123456")

    result = await admin_service._register_user(db, current_admin, req)

    assert result["msg"] == "新增用户成功"
    assert result["phone"] == "13800000000"
    assert db.flushed is True
    assert db.committed is True
    assert len(db.added) == 1
    assert db.added[0].source_channel_id is None
    assert db.added[0].channel_bound_at is None
    assert db.added[0].last_channel_visit_at is None
