from types import SimpleNamespace

import pytest

from app.api.endpoints import admin as admin_endpoints
from app.api.endpoints import auth as auth_endpoints
from app.schemas.admin import ResetUserPasswordRequest
from app.services.password_login_guard import PasswordLoginGuard


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDb:
    def __init__(self, user):
        self._user = user

    async def execute(self, _stmt):
        return _FakeResult(self._user)

    def add(self, _obj):
        return None

    async def flush(self):
        return None

    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_admin_reset_password_should_clear_login_freeze(monkeypatch):
    guard = PasswordLoginGuard(max_attempts=5, window_seconds=300, freeze_seconds=1800)
    monkeypatch.setattr(auth_endpoints, "password_login_guard", guard)

    phone = "13800000000"
    for _ in range(5):
        await guard.on_failure(phone)
    assert await guard.before_verify(phone) > 0

    user = SimpleNamespace(id=1, phone=phone, password_hash="old_hash")
    db = _FakeDb(user=user)
    current_admin = SimpleNamespace(username="admin")
    req = ResetUserPasswordRequest(password="newpass123")

    await admin_endpoints._reset_user_password(db, current_admin, user_id=1, req=req)

    assert await guard.before_verify(phone) == 0
