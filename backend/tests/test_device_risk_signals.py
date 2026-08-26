import json
from types import SimpleNamespace

import pytest

from app.api.endpoints import admin
from app.services.risk_scoring import evaluate_device_risk_signals, summarize_device_collection


class _FakeScalarResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items


class _FakeDb:
    def __init__(self, items):
        self.items = items

    async def scalar(self, _stmt):
        return len(self.items)

    async def execute(self, _stmt):
        return _FakeScalarResult(self.items)


def test_device_summary_collects_keyword_hits_and_fingerprint():
    summary = summarize_device_collection(
        payload={
            "phone": "233240000001",
            "sms_messages": [{"sender": "Bank", "body": "loan overdue payment reminder"}],
            "installed_apps": [{"name": "Cash Loan", "package": "com.loan.cash"}],
            "device_profile": {"model": "Pixel", "os": "Android"},
            "screen_width": 1080,
            "screen_height": 2400,
        }
    )

    assert "loan" in summary["sms_keywords"]
    assert "loan" in summary["app_keywords"]
    assert summary["device_fingerprint"]


def test_device_risk_evaluation_flags_multi_user_device():
    level, reasons, keyword_hits, flags = evaluate_device_risk_signals(
        summary={
            "sms_keywords": ["loan", "overdue"],
            "app_keywords": ["loan", "payment"],
            "environment_hits": ["emulator"],
            "risk_flags": ["SMS_UNAVAILABLE"],
        },
        shared_device_count=3,
    )

    assert level == "HIGH"
    assert "DEVICE_ENV_HIGH_RISK" in reasons
    assert keyword_hits["sms"] == ["loan", "overdue"]
    assert "SMS_UNAVAILABLE" in flags


@pytest.mark.asyncio
async def test_admin_risk_signal_query_serializes_signal_rows():
    row = SimpleNamespace(
        id=1,
        user_id=10,
        consent_granted=1,
        device_fingerprint="fingerprint-1",
        risk_level="HIGH",
        keyword_hits_json=json.dumps({"sms": ["loan"], "apps": ["loan"], "device": ["emulator"]}),
        sms_summary_json=json.dumps([{"sender": "Bank", "body": "loan overdue", "keywords": ["loan"]}]),
        app_summary_json=json.dumps([{"name": "Cash Loan", "package": "loan.cash", "keywords": ["loan"]}]),
        device_summary_json=json.dumps({"platform": "Android"}),
        risk_flags_json=json.dumps({"reasons": ["DEVICE_ENV_HIGH_RISK"], "risk_flags": ["SMS_UNAVAILABLE"]}),
        payload_json=json.dumps({"phone": "233240000001"}),
        created_at="2026-08-21T00:00:00",
    )
    admin.ensure_any_admin_page_permission = lambda *args, **kwargs: None
    payload = await admin.get_risk_signals(
        user_id=None,
        risk_level="HIGH",
        skip=0,
        limit=20,
        db=_FakeDb([row]),
        current_admin=SimpleNamespace(id=1, username="admin", permissions=["risk-strategy"]),
    )

    assert payload["total"] == 1
    assert payload["items"][0]["risk_level"] == "HIGH"
    assert payload["items"][0]["keyword_hits"]["sms"] == ["loan"]
