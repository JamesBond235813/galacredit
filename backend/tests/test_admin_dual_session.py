from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_admin_by_token_async
from app.api.endpoints import admin as admin_endpoints
from app.core.database import get_async_db
from app.core.security import get_password_hash


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDb:
    def __init__(self, admin):
        self.admin = admin
        self.commit_count = 0

    async def execute(self, _stmt):
        return _FakeResult(self.admin)

    async def commit(self):
        self.commit_count += 1


def _build_client(fake_db):
    app = FastAPI()
    app.include_router(admin_endpoints.router, prefix="/api/admin")

    async def _override_db():
        yield fake_db

    app.dependency_overrides[get_async_db] = _override_db
    return TestClient(app)


def _build_admin(username, password="secret123"):
    return SimpleNamespace(
        id=1,
        username=username,
        password_hash=get_password_hash(password),
        roles='["ADMIN"]',
        permissions=None,
        active_session_id=None,
        active_session_issued_at=None,
        active_web_session_id=None,
        active_web_session_issued_at=None,
        active_mobile_session_id=None,
        active_mobile_session_issued_at=None,
        created_at=None,
        updated_at=None,
    )


@pytest.mark.asyncio
async def test_xiaojiang_should_keep_web_and_mobile_sessions_online():
    admin = _build_admin("xiaojiang")
    fake_db = _FakeDb(admin)
    client = _build_client(fake_db)

    web_resp = client.post("/api/admin/login", json={"username": "xiaojiang", "password": "secret123"})
    mobile_resp = client.post(
        "/api/admin/login",
        json={"username": "xiaojiang", "password": "secret123", "client_type": "MOBILE"},
    )

    assert web_resp.status_code == 200
    assert mobile_resp.status_code == 200
    assert admin.active_web_session_id
    assert admin.active_mobile_session_id
    assert admin.active_web_session_id != admin.active_mobile_session_id
    assert await get_admin_by_token_async(fake_db, web_resp.json()["access_token"]) is admin
    assert await get_admin_by_token_async(fake_db, mobile_resp.json()["access_token"]) is admin


@pytest.mark.asyncio
async def test_normal_admin_should_keep_single_session_across_clients():
    admin = _build_admin("reviewer")
    fake_db = _FakeDb(admin)
    client = _build_client(fake_db)

    web_resp = client.post("/api/admin/login", json={"username": "reviewer", "password": "secret123"})
    mobile_resp = client.post(
        "/api/admin/login",
        json={"username": "reviewer", "password": "secret123", "client_type": "MOBILE"},
    )

    assert web_resp.status_code == 200
    assert mobile_resp.status_code == 200
    with pytest.raises(HTTPException):
        await get_admin_by_token_async(fake_db, web_resp.json()["access_token"])
    assert await get_admin_by_token_async(fake_db, mobile_resp.json()["access_token"]) is admin
