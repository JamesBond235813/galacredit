from datetime import datetime, timedelta

import httpx
import pytest

from app.services.ghana_risk import GhanaRiskClient


@pytest.mark.asyncio
async def test_ghana_submit_maps_filtered_sms_and_app_fields(monkeypatch):
    client = GhanaRiskClient()
    monkeypatch.setattr("app.services.ghana_risk.settings.GHANA_RISK_ENABLED", True)
    monkeypatch.setattr("app.services.ghana_risk.settings.GHANA_RISK_API_BASE_URL", "https://risk.example/xtable")
    monkeypatch.setattr("app.services.ghana_risk.settings.GHANA_RISK_CUSTOMER_ID", "merchant")
    monkeypatch.setattr("app.services.ghana_risk.settings.GHANA_RISK_CUSTOMER_SECRET_KEY", "secret")
    monkeypatch.setattr("app.services.ghana_risk.settings.GHANA_RISK_CALLBACK_URL", "https://app.example/api/user/risk-callback")
    captured = {}

    async def fake_post(self, url, json=None):
        captured["url"] = url
        captured["json"] = json
        return httpx.Response(200, json={"code": 200, "data": {"task_number": "Gh123", "message": "ok"}})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    result = await client.submit_task(
        request_id="req-1", apply_id="order-1", apply_time=__import__("datetime").datetime(2026, 9, 4, 12),
        sms_list=[
            {"address": "bank", "body": "loan", "type": 1, "time": "2026-09-01 12:00:00", "read": 0},
            {"address": "bank", "body": "loan", "type": 1, "time": (datetime.now() - timedelta(days=91)).strftime("%Y-%m-%d %H:%M:%S"), "read": 0},
            {"address": "bank", "body": "ordinary message", "type": 1, "time": "2026-09-01 12:00:00", "read": 0},
        ],
        app_list=[],
    )

    assert result["task_number"] == "Gh123"
    assert captured["url"].endswith("/gh_submit_data_v3")
    assert captured["json"]["risk_data"]["smsList"][0]["body"] == "loan"
    assert len(captured["json"]["risk_data"]["smsList"]) == 1
