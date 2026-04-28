from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import auth
from app.core.database import get_async_db
from app.core.security import get_password_hash
from app.services.password_login_guard import PasswordLoginGuard


class _Clock:
    def __init__(self):
        self.value = 0.0

    def now(self):
        return self.value


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDb:
    def __init__(self, user):
        self._user = user
        self.add_calls = 0

    async def execute(self, stmt):
        sql = str(stmt)
        if "FROM users" in sql:
            return _FakeResult(self._user)
        if "FROM oauth_clients" in sql:
            return _FakeResult(None)
        return _FakeResult(None)

    def add(self, _obj):
        self.add_calls += 1

    async def flush(self):
        return None

    async def commit(self):
        return None


def test_auth_login_should_not_auto_register_when_user_not_exists(monkeypatch):
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")
    fake_db = _FakeDb(user=None)

    async def _override_db():
        yield fake_db

    monkeypatch.setattr(
        auth,
        "password_login_guard",
        PasswordLoginGuard(max_attempts=5, window_seconds=300, freeze_seconds=1800),
    )
    app.dependency_overrides[get_async_db] = _override_db
    client = TestClient(app)

    resp = client.post("/api/auth/login", json={"phone": "13800000000", "password": "badpass1"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "用户或密码不正确"
    assert fake_db.add_calls == 0


def test_auth_login_should_freeze_after_five_failed_attempts(monkeypatch):
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")
    user = SimpleNamespace(id=1, phone="13800000000", password_hash=get_password_hash("rightpass"))
    fake_db = _FakeDb(user=user)
    clock = _Clock()

    async def _override_db():
        yield fake_db

    monkeypatch.setattr(
        auth,
        "password_login_guard",
        PasswordLoginGuard(
            max_attempts=5,
            window_seconds=300,
            freeze_seconds=1800,
            now_provider=clock.now,
        ),
    )
    app.dependency_overrides[get_async_db] = _override_db
    client = TestClient(app)

    for _ in range(4):
        resp = client.post("/api/auth/login", json={"phone": "13800000000", "password": "wrongpass"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "用户或密码不正确"

    last_try = client.post("/api/auth/login", json={"phone": "13800000000", "password": "wrongpass"})
    assert last_try.status_code == 400
    assert "由于密码输入错误次数过多" in last_try.json()["detail"]

    frozen_try = client.post("/api/auth/login", json={"phone": "13800000000", "password": "rightpass"})
    assert frozen_try.status_code == 400
    assert "由于密码输入错误次数过多" in frozen_try.json()["detail"]
