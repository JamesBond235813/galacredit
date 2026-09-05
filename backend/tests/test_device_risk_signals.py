import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.api.endpoints import admin
from app.services.risk_scoring import evaluate_device_risk_signals, summarize_device_collection
from app.services.sms_filter import filter_sms_messages, match_sms_keywords, sms_collection_allowed


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
            "sms_messages": [{"sender": "Bank", "body": "loan overdue payment reminder", "time": "2026-09-01 12:00:00"}],
            "installed_apps": [{"name": "Cash Loan", "package": "com.loan.cash"}],
            "device_profile": {"model": "Pixel", "os": "Android"},
            "screen_width": 1080,
            "screen_height": 2400,
        }
    )

    assert "loan" in summary["sms_keywords"]
    assert "loan" in summary["app_keywords"]
    assert summary["device_fingerprint"]


@pytest.mark.asyncio
async def test_record_device_signal_does_not_persist_raw_device_identifier():
    from app.services import risk_scoring

    class FakeDb:
        def add(self, value):
            self.value = value

        async def flush(self):
            self.value.id = 1

    db = FakeDb()
    await risk_scoring.record_device_signal(
        db,
        user_id=1,
        payload={
            "phone": "233240000001",
            "ip_address": "198.51.100.10",
            "device_fingerprint": "raw-android-id",
            "device_profile": {"model": "Pixel"},
        },
    )
    assert "raw-android-id" not in db.value.payload_json
    assert "233240000001" not in db.value.payload_json
    assert "198.51.100.10" not in db.value.payload_json


def test_sms_filter_uses_csv_regex_and_90_day_window():
    now = datetime(2026, 9, 4, 12, 0, 0)
    rows = filter_sms_messages([
        {"sender": "Bank", "body": "Your loan is approved", "time": "2026-09-01 12:00:00"},
        {"sender": "Bank", "body": "loan approved", "time": (now - timedelta(days=91)).strftime("%Y-%m-%d %H:%M:%S")},
        {"sender": "Bank", "body": "loanapproved", "time": "2026-09-01 12:00:00"},
    ], now=now, keywords=["loan", "approved"])

    assert len(rows) == 1
    assert rows[0]["keywords"] == ["loan", "approved"]
    assert match_sms_keywords("loanapproved", ["loan"]) == []


def test_sms_filter_uses_ascii_boundaries_like_mobile_clients():
    assert match_sms_keywords("贷款loan提醒", ["loan"]) == ["loan"]
    assert match_sms_keywords("loanapproved", ["loan"]) == []


def test_sms_collection_requires_internal_android_channel_and_consent():
    assert sms_collection_allowed(
        platform="Android",
        app_channel="internal",
        consent_sms=True,
        native_bridge="GalaCreditNativeRisk",
        source="NATIVE_ANDROID",
    )
    assert not sms_collection_allowed(platform="Android", app_channel="play", consent_sms=True)
    assert not sms_collection_allowed(platform="iOS", app_channel="internal", consent_sms=True)
    assert not sms_collection_allowed(platform="Android", app_channel="internal", consent_sms=False)
    assert not sms_collection_allowed(
        platform="Android",
        app_channel="internal",
        consent_sms=True,
        native_bridge="spoofed-page",
        source="NATIVE_ANDROID",
    )


def test_sms_filter_bounds_rows_and_sanitizes_malformed_flags():
    now = datetime(2026, 9, 4, 12, 0, 0)
    rows = [
        {"sender": "Bank", "body": "loan approved", "time": now, "type": "invalid", "read": "invalid"}
    ] + [
        {"sender": "Bank", "body": "loan approved", "time": now}
        for _ in range(5001)
    ]

    filtered = filter_sms_messages(rows, now=now, keywords=["loan"])

    assert len(filtered) == 5000
    assert filtered[0]["type"] == 1
    assert filtered[0]["read"] == 0


def test_sms_filter_accepts_numeric_millisecond_timestamp():
    now = datetime(2026, 9, 4, 12, 0, 0)
    timestamp = int(now.timestamp() * 1000)

    filtered = filter_sms_messages(
        [{"sender": "Bank", "body": "loan approved", "timestamp": timestamp}],
        now=now,
        keywords=["loan"],
    )

    assert len(filtered) == 1


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
