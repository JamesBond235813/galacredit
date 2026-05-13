import asyncio

from app.services import sms_service


def test_sms_service_should_enforce_cooldown_by_phone_and_biz(monkeypatch):
    monkeypatch.setattr(sms_service.settings, "SMS_CODE_MOCK_ENABLED", True)
    service = sms_service.SmsService()
    now = {"value": 1000.0}
    monkeypatch.setattr(sms_service.SmsService, "_now", staticmethod(lambda: now["value"]))

    ok1, cooldown1, _ = asyncio.run(service.send_code("13800000000", "ORDER"))
    assert ok1 is True
    assert cooldown1 == 60

    ok2, cooldown2, message2 = asyncio.run(service.send_code("13800000000", "ORDER"))
    assert ok2 is False
    assert cooldown2 >= 1
    assert "发送过于频繁" in message2


def test_sms_service_should_allow_different_biz_type(monkeypatch):
    monkeypatch.setattr(sms_service.settings, "SMS_CODE_MOCK_ENABLED", True)
    service = sms_service.SmsService()
    now = {"value": 2000.0}
    monkeypatch.setattr(sms_service.SmsService, "_now", staticmethod(lambda: now["value"]))

    ok1, _, _ = asyncio.run(service.send_code("13800000000", "ORDER"))
    ok2, _, _ = asyncio.run(service.send_code("13800000000", "LOGIN"))
    assert ok1 is True
    assert ok2 is True


def test_sms_service_should_verify_and_consume_code(monkeypatch):
    monkeypatch.setattr(sms_service.settings, "SMS_CODE_MOCK_ENABLED", True)
    service = sms_service.SmsService()
    now = {"value": 3000.0}
    monkeypatch.setattr(sms_service.SmsService, "_now", staticmethod(lambda: now["value"]))

    ok, _, _ = asyncio.run(service.send_code("13800000000", "ORDER"))
    assert ok is True

    assert asyncio.run(service.verify_code("13800000000", "ORDER", "000000")) is False
    assert asyncio.run(service.verify_code("13800000000", "ORDER", "635147")) is True
    assert asyncio.run(service.verify_code("13800000000", "ORDER", "635147")) is False
