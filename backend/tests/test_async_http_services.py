import httpx
import pytest

from app.services.esign_identity import ESignIdentityClient
from app.services.location import reverse_geocode


@pytest.mark.asyncio
async def test_esign_http_request_uses_async_client(monkeypatch):
    class DummyResponse:
        def __init__(self):
            self.status_code = 200
            self.text = '{"code":0,"data":{"ok":true}}'

        def json(self):
            return {"code": 0, "data": {"ok": True}}

        def raise_for_status(self):
            return None

    called = {"value": False}

    async def fake_request(self, method, url, content=None, headers=None):
        called["value"] = True
        return DummyResponse()

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    client = ESignIdentityClient()
    monkeypatch.setattr(client, "ensure_configured", lambda: None)
    monkeypatch.setattr(client, "_build_signature_headers", lambda *args, **kwargs: {"x-test": "1"})

    resp = await client._http_request("POST", "/v2/test", body={"name": "foo"})
    assert called["value"] is True
    assert resp["code"] == 0


@pytest.mark.asyncio
async def test_reverse_geocode_is_async_httpx(monkeypatch):
    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "display_name": "广东省深圳市南山区科技园",
                "address": {
                    "state": "广东省",
                    "city": "深圳市",
                    "county": "南山区",
                    "road": "科技园路",
                },
            }

    async def fake_get(self, url, params=None, headers=None, timeout=None):
        return DummyResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = await reverse_geocode(latitude=22.543096, longitude=114.057865)
    assert result["province"] == "广东省"
    assert result["city"] == "深圳市"
    assert result["district"] == "南山区"
