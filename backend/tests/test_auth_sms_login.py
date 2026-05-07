from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import auth
from app.core.database import get_async_db


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDb:
    def __init__(self, user=None, channel=None):
        self._user = user
        self._channel = channel
        self.added_users = []

    async def execute(self, stmt):
        sql = str(stmt)
        if "FROM users" in sql:
            return _FakeResult(self._user)
        if "FROM channels" in sql:
            return _FakeResult(self._channel)
        return _FakeResult(None)

    def add(self, obj):
        self.added_users.append(obj)
        self._user = obj

    async def flush(self):
        if self._user and not getattr(self._user, "id", None):
            self._user.id = 100
        return None

    async def commit(self):
        return None


class _FakeSmsService:
    def __init__(self, ok=True):
        self.ok = ok

    async def verify_code(self, phone: str, biz_type: str, code: str):
        return self.ok and biz_type == "LOGIN" and code == "123456"


def _build_app(fake_db):
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")

    async def _override_db():
        yield fake_db

    app.dependency_overrides[get_async_db] = _override_db
    return app


def test_sms_login_should_register_new_user_and_bind_channel(monkeypatch):
    fake_db = _FakeDb(user=None, channel=SimpleNamespace(id=8, channel_name="c1", sales_name="s1", status="ACTIVE"))
    monkeypatch.setattr(auth, "sms_service", _FakeSmsService(ok=True))
    async def _fake_upsert(*args, **kwargs):
        return None

    async def _fake_log(*args, **kwargs):
        return None

    async def _fake_issue(*args, **kwargs):
        return {
            "access_token": "a",
            "refresh_token": "r",
            "token_type": "bearer",
            "access_token_expires_at": "2026-01-01T00:00:00",
            "refresh_token_expires_at": "2026-01-01T00:00:00",
        }

    monkeypatch.setattr(auth, "_upsert_oauth_client", _fake_upsert)
    monkeypatch.setattr(auth, "log_user_event_async", _fake_log)
    monkeypatch.setattr(auth, "_issue_user_token_pair", _fake_issue)

    async def _fake_bind_user_source_channel_async(db, *, user, channel, loan):
        user.source_channel_id = channel.id
        return "BOUND"

    monkeypatch.setattr(auth, "bind_user_source_channel_async", _fake_bind_user_source_channel_async)
    app = _build_app(fake_db)
    client = TestClient(app)

    resp = client.post(
        "/api/auth/sms-login",
        json={"phone": "13800000000", "sms_code": "123456", "invite_code": "abcd1234abcd5678"},
    )
    assert resp.status_code == 200
    assert len(fake_db.added_users) == 1
    assert getattr(fake_db._user, "source_channel_id", None) == 8


def test_sms_login_should_ignore_invite_code_for_existing_user(monkeypatch):
    existing_user = SimpleNamespace(id=10, phone="13800000000", source_channel_id=3, last_login_at=None)
    fake_db = _FakeDb(user=existing_user, channel=SimpleNamespace(id=8, channel_name="c1", sales_name="s1", status="ACTIVE"))
    monkeypatch.setattr(auth, "sms_service", _FakeSmsService(ok=True))
    async def _fake_upsert(*args, **kwargs):
        return None

    async def _fake_log(*args, **kwargs):
        return None

    async def _fake_issue(*args, **kwargs):
        return {
            "access_token": "a",
            "refresh_token": "r",
            "token_type": "bearer",
            "access_token_expires_at": "2026-01-01T00:00:00",
            "refresh_token_expires_at": "2026-01-01T00:00:00",
        }

    monkeypatch.setattr(auth, "_upsert_oauth_client", _fake_upsert)
    monkeypatch.setattr(auth, "log_user_event_async", _fake_log)
    monkeypatch.setattr(auth, "_issue_user_token_pair", _fake_issue)

    async def _fake_bind_user_source_channel_async(db, *, user, channel, loan):
        user.source_channel_id = channel.id
        return "BOUND"

    monkeypatch.setattr(auth, "bind_user_source_channel_async", _fake_bind_user_source_channel_async)
    app = _build_app(fake_db)
    client = TestClient(app)

    resp = client.post(
        "/api/auth/sms-login",
        json={"phone": "13800000000", "sms_code": "123456", "invite_code": "abcd1234abcd5678"},
    )
    assert resp.status_code == 200
    assert fake_db._user.source_channel_id == 3
    assert len(fake_db.added_users) == 0
