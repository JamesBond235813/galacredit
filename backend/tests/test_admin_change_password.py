from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import admin_service
from app.schemas.admin import AdminChangePasswordRequest


class _FakeDb:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_change_admin_password_should_reject_wrong_old_password(monkeypatch):
    monkeypatch.setattr(admin_service, "verify_password", lambda *_args, **_kwargs: False)

    db = _FakeDb()
    admin = SimpleNamespace(password_hash="hashed-old")
    req = AdminChangePasswordRequest(old_password="old123", new_password="new123", confirm_password="new123")

    with pytest.raises(HTTPException) as exc_info:
        await admin_service._change_admin_password(db, admin, req)

    assert exc_info.value.status_code == 400
    assert db.committed is False


@pytest.mark.asyncio
async def test_change_admin_password_should_update_password(monkeypatch):
    monkeypatch.setattr(admin_service, "verify_password", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(admin_service, "get_password_hash", lambda value: f"hashed:{value}")

    db = _FakeDb()
    admin = SimpleNamespace(password_hash="hashed-old")
    req = AdminChangePasswordRequest(old_password="old123", new_password="new123", confirm_password="new123")

    result = await admin_service._change_admin_password(db, admin, req)

    assert result["msg"] == "修改密码成功"
    assert admin.password_hash == "hashed:new123"
    assert db.committed is True
