import pytest

from app.core.config import settings
from app.services.ghana_identity import GhanaIdentityError, GhanaCardIdentityProvider


@pytest.mark.asyncio
async def test_ghana_card_mock_returns_localized_identity(monkeypatch):
    monkeypatch.setattr(settings, "GHANA_IDENTITY_ENABLED", False)
    monkeypatch.setattr(settings, "GHANA_IDENTITY_MOCK_ENABLED", True)

    result = await GhanaCardIdentityProvider().ocr(b"front-image")

    assert result["name"] == "Ama Mensah"
    assert result["id_card_num"].startswith("GHA-")
    assert result["id_address"] == "Accra, Ghana"


@pytest.mark.asyncio
async def test_ghana_card_real_provider_is_reserved_until_configured(monkeypatch):
    monkeypatch.setattr(settings, "GHANA_IDENTITY_ENABLED", True)
    monkeypatch.setattr(settings, "GHANA_IDENTITY_MOCK_ENABLED", False)

    with pytest.raises(GhanaIdentityError, match="reserved but not configured"):
        await GhanaCardIdentityProvider().ocr(b"front-image")


@pytest.mark.asyncio
async def test_ghana_card_face_mock_passes(monkeypatch):
    monkeypatch.setattr(settings, "GHANA_IDENTITY_ENABLED", False)
    monkeypatch.setattr(settings, "GHANA_IDENTITY_MOCK_ENABLED", True)

    result = await GhanaCardIdentityProvider().face_compare("Ama Mensah", "GHA-000000000-0", b"face")

    assert result["passed"] is True
    assert result["score"] == 0.99
