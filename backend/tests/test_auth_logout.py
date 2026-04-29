from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import auth
from app.core.database import get_async_db


class _FakeResult:
    def scalar_one_or_none(self):
        return None


class _FakeDb:
    def __init__(self):
        self.update_called = False
        self.commit_called = False

    async def execute(self, stmt):
        sql = str(stmt)
        if "UPDATE oauth_tokens" in sql:
            self.update_called = True
        return _FakeResult()

    async def commit(self):
        self.commit_called = True


def test_auth_logout_should_revoke_tokens():
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")
    fake_db = _FakeDb()

    async def _override_db():
        yield fake_db

    app.dependency_overrides[get_async_db] = _override_db
    client = TestClient(app)

    resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer access-token-abc"},
        json={"refresh_token": "refresh-token-abcdefghijklmnopqrstuvwxyz"},
    )

    assert resp.status_code == 200
    assert resp.json()["msg"] == "退出成功"
    assert fake_db.update_called is True
    assert fake_db.commit_called is True


def test_auth_logout_should_return_success_when_access_token_missing():
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")
    fake_db = _FakeDb()

    async def _override_db():
        yield fake_db

    app.dependency_overrides[get_async_db] = _override_db
    client = TestClient(app)

    resp = client.post(
        "/api/auth/logout",
        json={"refresh_token": "refresh-token-abcdefghijklmnopqrstuvwxyz"},
    )

    assert resp.status_code == 200
    assert resp.json()["msg"] == "退出成功"
    assert fake_db.update_called is False
    assert fake_db.commit_called is False
