import httpx
import pytest

from app.services import momo


@pytest.mark.asyncio
async def test_hubtel_collect_uses_async_checkout_request(monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"responseCode": "200", "data": {"checkoutId": "CHK-1"}, "message": "ok"}

    async def fake_post(self, url, **kwargs):
        calls.update(url=url, kwargs=kwargs)
        return FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    provider = momo.HubtelMomoProvider()
    result = await provider.collect("233240000001", 12.5, 8)

    assert result.success is True
    assert result.reference == "CHK-1"
    assert calls["url"] == momo.settings.HUBTEL_INITIATE_URL
    assert calls["kwargs"]["json"]["totalAmount"] == 12.5


@pytest.mark.asyncio
async def test_hubtel_disbursement_is_explicitly_unsupported():
    result = await momo.HubtelMomoProvider().disburse("233240000001", 10, 1)
    assert result.success is False
    assert "不支持放款" in result.message
