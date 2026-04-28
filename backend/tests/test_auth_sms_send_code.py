from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import auth
from app.services.sms_auth import SmsAuthManager


def test_send_code_should_return_cooldown_and_block_repeat_request(monkeypatch):
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")

    manager = SmsAuthManager(
        phone_cooldown_seconds=60,
        ip_rate_limit_per_minute=10,
        code_expire_seconds=300,
        mock_enabled=True,
        mock_code="635147",
    )
    monkeypatch.setattr(auth, "sms_auth_manager", manager)

    client = TestClient(app)
    first = client.post("/api/auth/send-code", json={"phone": "13800000000"})
    assert first.status_code == 200
    assert first.json()["cooldown_seconds"] == 60

    second = client.post("/api/auth/send-code", json={"phone": "13800000000"})
    assert second.status_code == 429
    assert "发送过于频繁" in second.json()["detail"]
