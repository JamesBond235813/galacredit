from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user_async
from app.api.endpoints import user
from app.core.database import get_async_db


class _FakeDb:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None

    async def commit(self):
        self.committed = True


def _build_app(fake_db, fake_user):
    app = FastAPI()
    app.include_router(user.router, prefix="/api/user")

    async def _override_db():
        yield fake_db

    async def _override_user():
        return fake_user

    app.dependency_overrides[get_async_db] = _override_db
    app.dependency_overrides[get_current_user_async] = _override_user
    return app


def test_capture_risk_signals_persists_summary(monkeypatch):
    fake_db = _FakeDb()
    fake_user = SimpleNamespace(id=9, phone="233240000001")

    async def _fake_record_device_signal(db, *, user_id, payload):
        return SimpleNamespace(
            id=11,
            user_id=user_id,
            device_fingerprint="fp-11",
            risk_level="MEDIUM",
            keyword_hits_json='{"sms":["loan"],"apps":[],"device":[]}',
            risk_flags_json='{"risk_flags":["SMS_UNAVAILABLE"]}',
        )

    async def _fake_log_user_event_async(*args, **kwargs):
        return None

    monkeypatch.setattr(user, "record_device_signal", _fake_record_device_signal)
    monkeypatch.setattr(user, "log_user_event_async", _fake_log_user_event_async)

    client = TestClient(_build_app(fake_db, fake_user))
    resp = client.post(
        "/api/user/risk-signals",
        json={
            "phone": "233240000001",
            "accepted_user_agreement": True,
            "accepted_personal_authorization": True,
            "accepted_sensitive_collection": True,
            "device_payload": {
                "consent_sms": True,
                "consent_app_list": True,
                "consent_device_fingerprint": True,
                "sms_messages": [{"sender": "bank", "body": "loan overdue"}],
                "installed_apps": [{"name": "Cash Loan", "package": "loan.cash"}],
                "device_profile": {"model": "Pixel"},
                "source": "NATIVE"
            }
        }
    )

    assert resp.status_code == 200
    assert resp.json()["risk_level"] == "MEDIUM"
    assert fake_db.committed is True


def test_capture_risk_signals_drops_unimplemented_app_list(monkeypatch):
    fake_db = _FakeDb()
    fake_user = SimpleNamespace(id=9, phone="233240000001")
    captured = {}

    async def _fake_record_device_signal(db, *, user_id, payload):
        captured["payload"] = payload
        return SimpleNamespace(
            id=12,
            user_id=user_id,
            device_fingerprint="fp-12",
            risk_level="LOW",
            keyword_hits_json='{"sms": [], "apps": [], "device": []}',
            risk_flags_json='{"risk_flags": []}',
        )

    async def _fake_log_user_event_async(*args, **kwargs):
        return None

    monkeypatch.setattr(user, "record_device_signal", _fake_record_device_signal)
    monkeypatch.setattr(user, "log_user_event_async", _fake_log_user_event_async)

    client = TestClient(_build_app(fake_db, fake_user))
    response = client.post(
        "/api/user/risk-signals",
        json={
            "phone": "233240000001",
            "accepted_user_agreement": True,
            "accepted_personal_authorization": True,
            "accepted_sensitive_collection": True,
            "device_payload": {
                "consent_app_list": True,
                "installed_apps": [{"name": "Secret app", "package": "com.example.secret"}],
                "device_profile": {"model": "Pixel"},
                "source": "NATIVE",
            },
        },
    )

    assert response.status_code == 200
    assert captured["payload"]["installed_apps"] == []


def test_capture_risk_signals_drops_sms_for_play_channel(monkeypatch):
    fake_db = _FakeDb()
    fake_user = SimpleNamespace(id=9, phone="233240000001")
    captured = {}

    async def _fake_record_device_signal(db, *, user_id, payload):
        captured["payload"] = payload
        return SimpleNamespace(
            id=13,
            user_id=user_id,
            device_fingerprint="fp-13",
            risk_level="LOW",
            keyword_hits_json='{"sms": [], "apps": [], "device": []}',
            risk_flags_json='{"risk_flags": []}',
        )

    async def _fake_submit_task(**kwargs):
        captured["sms_list"] = kwargs["sms_list"]
        return {"status": "SKIPPED", "reason": "test"}

    async def _fake_log_user_event_async(*args, **kwargs):
        return None

    monkeypatch.setattr(user, "record_device_signal", _fake_record_device_signal)
    monkeypatch.setattr(user, "log_user_event_async", _fake_log_user_event_async)
    monkeypatch.setattr(user.ghana_risk_client, "submit_task", _fake_submit_task)

    client = TestClient(_build_app(fake_db, fake_user))
    response = client.post(
        "/api/user/risk-signals",
        json={
            "phone": "233240000001",
            "accepted_user_agreement": True,
            "accepted_personal_authorization": True,
            "accepted_sensitive_collection": True,
            "device_payload": {
                "platform": "Android",
                "app_channel": "play",
                "consent_sms": True,
                "sms_messages": [{"address": "Bank", "body": "loan approved", "time": "2026-09-01 12:00:00"}],
                "source": "NATIVE",
            },
        },
    )

    assert response.status_code == 200
    assert captured["payload"]["sms_messages"] == []
    assert captured["payload"]["consent_sms"] is False
    assert captured["sms_list"] == []


def test_capture_risk_signals_allows_filtered_sms_only_for_trusted_internal_bridge(monkeypatch):
    fake_db = _FakeDb()
    fake_user = SimpleNamespace(id=9, phone="233240000001")
    captured = {}

    async def _fake_record_device_signal(db, *, user_id, payload):
        captured["payload"] = payload
        return SimpleNamespace(
            id=14,
            user_id=user_id,
            device_fingerprint="fp-14",
            risk_level="MEDIUM",
            keyword_hits_json='{"sms":["loan"],"apps":[],"device":[]}',
            risk_flags_json='{"risk_flags":[]}',
        )

    async def _fake_submit_task(**kwargs):
        captured["sms_list"] = kwargs["sms_list"]
        return {"status": "SUCCESS", "task_number": "Gh-internal"}

    async def _fake_log_user_event_async(*args, **kwargs):
        return None

    monkeypatch.setattr(user, "record_device_signal", _fake_record_device_signal)
    monkeypatch.setattr(user, "log_user_event_async", _fake_log_user_event_async)
    monkeypatch.setattr(user.ghana_risk_client, "submit_task", _fake_submit_task)

    client = TestClient(_build_app(fake_db, fake_user))
    response = client.post(
        "/api/user/risk-signals",
        json={
            "phone": "233240000001",
            "accepted_user_agreement": True,
            "accepted_personal_authorization": True,
            "accepted_sensitive_collection": True,
            "device_payload": {
                "platform": "android",
                "app_channel": "internal",
                "native_bridge": "GalaCreditNativeRisk",
                "source": "NATIVE_ANDROID",
                "consent_sms": True,
                "sms_messages": [{"address": "Bank", "body": "loan approved", "time": "2026-09-01 12:00:00"}],
            },
        },
    )

    assert response.status_code == 200
    assert captured["payload"]["consent_sms"] is True
    assert captured["sms_list"][0]["body"] == "loan approved"
