from types import SimpleNamespace

import pytest

from app.schemas.channel import ChannelCreateRequest, ChannelUpdateRequest
from app.services.channel_service import normalize_channel_disbursement_mode


def test_normalize_channel_disbursement_mode_defaults_to_manual():
    assert normalize_channel_disbursement_mode(None) == "MANUAL_DISBURSE"
    assert normalize_channel_disbursement_mode("auto_disburse") == "AUTO_DISBURSE"


def test_channel_schema_accepts_auto_mode_and_rejects_invalid_mode():
    request = ChannelCreateRequest(
        channel_name="test_channel",
        sales_name="Advisor",
        admin_user_id=1,
        disbursement_mode="AUTO_DISBURSE",
    )
    assert request.disbursement_mode == "AUTO_DISBURSE"

    with pytest.raises(ValueError):
        ChannelUpdateRequest(disbursement_mode="UNKNOWN")


def test_channel_serialization_keeps_legacy_channels_manual(monkeypatch):
    from app.services import admin_service

    channel = SimpleNamespace(
        id=1,
        channel_name="test_channel",
        invite_code="abc123def456gh78",
        sales_name="Advisor",
        status="ACTIVE",
        note=None,
        created_at=None,
        users=[],
        admin_user_id=None,
    )

    payload = admin_service.serialize_channel(channel)

    assert payload["disbursement_mode"] == "MANUAL_DISBURSE"
