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
    class _FakeSliderCaptchaManager:
        async def consume_ticket(self, phone: str, ticket: str):
            return ticket == "ok-ticket-01"

    class _FakeSmsService:
        async def send_code(self, phone: str, biz_type: str):
            return True, 60, "验证码发送成功"

    monkeypatch.setattr(auth, "sms_auth_manager", manager)
    monkeypatch.setattr(auth, "slider_captcha_manager", _FakeSliderCaptchaManager())
    monkeypatch.setattr(auth, "sms_service", _FakeSmsService())

    client = TestClient(app)
    first = client.post("/api/auth/send-code", json={"phone": "13800000000", "captcha_ticket": "ok-ticket-01"})
    assert first.status_code == 200
    assert first.json()["cooldown_seconds"] == 60

    second = client.post("/api/auth/send-code", json={"phone": "13800000000", "captcha_ticket": "ok-ticket-01"})
    assert second.status_code == 429
    assert "发送过于频繁" in second.json()["detail"]


def test_send_code_should_use_x_forwarded_for_ip(monkeypatch):
    class _FakeManager:
        def __init__(self):
            self.received_ip = None

        async def issue_code(self, phone: str, ip: str):
            self.received_ip = ip
            return True, 60

    class _FakeSliderCaptchaManager:
        async def consume_ticket(self, phone: str, ticket: str):
            return ticket == "ok-ticket-01"

    class _FakeSmsService:
        async def send_code(self, phone: str, biz_type: str):
            return True, 60, "验证码发送成功"

    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")
    manager = _FakeManager()
    monkeypatch.setattr(auth, "sms_auth_manager", manager)
    monkeypatch.setattr(auth, "slider_captcha_manager", _FakeSliderCaptchaManager())
    monkeypatch.setattr(auth, "sms_service", _FakeSmsService())

    client = TestClient(app)
    resp = client.post(
        "/api/auth/send-code",
        json={"phone": "13800000000", "captcha_ticket": "ok-ticket-01"},
        headers={"X-Forwarded-For": "1.2.3.4, 10.0.0.1"},
    )
    assert resp.status_code == 200
    assert manager.received_ip == "1.2.3.4"
