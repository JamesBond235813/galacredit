import httpx
import pytest

from app.services import location
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

    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_PROVIDER", "nominatim")
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = await reverse_geocode(latitude=22.543096, longitude=114.057865)
    assert result["province"] == "广东省"
    assert result["city"] == "深圳市"
    assert result["district"] == "南山区"


@pytest.mark.asyncio
async def test_reverse_geocode_uses_aliyun_market_appcode(monkeypatch):
    class DummyResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "code": "0",
                "data": {
                    "address": "广东省深圳市南山区科技园",
                    "province": "广东省",
                    "city": "深圳市",
                    "district": "南山区",
                    "street": "科技园路",
                },
            }

    captured = {}

    async def fake_request(self, method, url, params=None, data=None, headers=None, timeout=None):
        captured["method"] = method
        captured["url"] = url
        captured["params"] = params
        captured["data"] = data
        captured["headers"] = headers
        return DummyResponse()

    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_PROVIDER", "aliyun_market")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_API_URL", "https://example.test/geocode")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_APP_CODE", "test-app-code")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_HTTP_METHOD", "POST")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_LOCATION_PARAM", "")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_LAT_PARAM", "latitude")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_LNG_PARAM", "longitude")
    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    result = await reverse_geocode(latitude=22.543096, longitude=114.057865)

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.test/geocode"
    assert captured["params"] is None
    assert captured["data"] == {"latitude": "22.5430960", "longitude": "114.0578650"}
    assert captured["headers"]["Authorization"] == "APPCODE test-app-code"
    assert result["province"] == "广东省"
    assert result["city"] == "深圳市"
    assert result["district"] == "南山区"


@pytest.mark.asyncio
async def test_reverse_geocode_supports_combined_location_param(monkeypatch):
    class DummyResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": {
                    "regeocodes": [
                        {
                            "formatted_address": "广东省深圳市福田区莲花街道深圳市人民政府",
                            "addressComponent": {
                                "province": "广东省",
                                "city": "深圳市",
                                "district": "福田区",
                                "streetNumber": {"street": "福中三路"},
                            },
                        }
                    ]
                }
            }

    captured = {}

    async def fake_request(self, method, url, params=None, data=None, headers=None, timeout=None):
        captured["data"] = data
        return DummyResponse()

    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_PROVIDER", "aliyun_market")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_API_URL", "https://example.test/geocode")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_APP_CODE", "test-app-code")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_HTTP_METHOD", "POST")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_LOCATION_PARAM", "location")
    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    result = await reverse_geocode(latitude=22.543096, longitude=114.057865)

    assert captured["data"] == {"location": "114.0578650,22.5430960"}
    assert result["address"] == "广东省深圳市福田区莲花街道深圳市人民政府"
    assert result["district"] == "福田区"


@pytest.mark.asyncio
async def test_reverse_geocode_marks_unresolved_when_aliyun_market_returns_empty(monkeypatch):
    class EmptyAliyunResponse:
        status_code = 403

        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "403 Forbidden",
                request=httpx.Request("POST", "https://example.test/geocode"),
                response=httpx.Response(403),
            )

        def json(self):
            return {}

    called = {"request": 0, "get": 0}

    async def fake_request(self, method, url, params=None, data=None, headers=None, timeout=None):
        called["request"] += 1
        return EmptyAliyunResponse()

    async def fake_get(self, url, params=None, headers=None, timeout=None):
        called["get"] += 1
        raise AssertionError("阿里云GPS反解析失败后不应使用其他地址源兜底")

    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_PROVIDER", "aliyun_market")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_API_URL", "https://example.test/geocode")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_APP_CODE", "test-app-code")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_HTTP_METHOD", "POST")
    monkeypatch.setattr(location.settings, "LOCATION_GEOCODE_LOCATION_PARAM", "location")
    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = await reverse_geocode(latitude=31.220008, longitude=119.130996)

    assert called == {"request": 1, "get": 0}
    assert result["address"] == "GPS无法解析"
    assert result["province"] is None
    assert result["city"] is None
    assert result["district"] is None
