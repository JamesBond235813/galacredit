from datetime import datetime
from types import SimpleNamespace

import pytest

from app.services import admin_service


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _ScalarsResult:
    def __init__(self, values):
        self._values = values

    def unique(self):
        return self

    def scalars(self):
        return self

    def all(self):
        return self._values


class _FakeDbForChannels:
    def __init__(self, channels, advisors):
        self._channels = channels
        self._advisors = advisors
        self._execute_count = 0

    async def execute(self, _stmt):
        self._execute_count += 1
        if self._execute_count == 1:
            return _ScalarsResult(self._channels)
        return _ScalarsResult(self._advisors)


class _FakeUniqueResult:
    def __init__(self, value):
        self._value = value

    def unique(self):
        return self

    def scalar_one_or_none(self):
        return self._value


class _FakeDbForUpdateChannelInviteCode:
    def __init__(self, channel, advisor):
        self._channel = channel
        self._advisor = advisor
        self.committed = False
        self._execute_count = 0

    async def execute(self, stmt):
        self._execute_count += 1
        if self._execute_count == 1:
            return _FakeUniqueResult(self._channel)
        if self._execute_count == 2:
            return _ScalarResult(None)
        if self._execute_count == 3:
            return _ScalarResult(self._advisor)
        return _ScalarResult(None)

    async def commit(self):
        self.committed = True

    async def refresh(self, _obj):
        return None


def test_serialize_channel_should_include_invite_code():
    channel = SimpleNamespace(
        id=1,
        channel_name="test_channel",
        invite_code="abc123def456gh78",
        sales_name="顾问A",
        status="ACTIVE",
        note="n",
        created_at=datetime(2026, 5, 7, 10, 0, 0),
        users=[],
        admin_user_id=2,
    )
    advisor = SimpleNamespace(id=2, username="advisor")

    payload = admin_service.serialize_channel(channel, advisor)

    assert payload["invite_code"] == "abc123def456gh78"
    assert payload["admin_user_name"] == "advisor"


def test_generate_channel_invite_code_should_include_letters_and_digits():
    code = admin_service._generate_channel_invite_code(16)

    assert len(code) == 16
    assert code.isalnum()
    assert code.lower() == code
    assert any(char.isalpha() for char in code)
    assert any(char.isdigit() for char in code)


@pytest.mark.asyncio
async def test_get_channels_should_return_channel_link_prefix(monkeypatch):
    monkeypatch.setattr(admin_service, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin_service.settings, "CHANNEL_LINK_PREFIX", "https://h5.example.com")
    current_admin = SimpleNamespace(id=10, username="admin", roles='["ADMIN"]')
    channel = SimpleNamespace(
        id=1,
        channel_name="test_channel",
        invite_code="abc123def456gh78",
        sales_name="顾问A",
        status="ACTIVE",
        note="",
        created_at=datetime(2026, 5, 7, 10, 0, 0),
        users=[],
        admin_user_id=2,
    )
    advisor = SimpleNamespace(id=2, username="advisor")
    db = _FakeDbForChannels([channel], [advisor])

    payload = await admin_service._get_channels(db, current_admin, keyword=None, status="ALL", skip=0, limit=10)

    assert payload["channel_link_prefix"] == "https://h5.example.com"
    assert payload["items"][0]["invite_code"] == "abc123def456gh78"


@pytest.mark.asyncio
async def test_update_channel_should_auto_generate_invite_code_when_empty(monkeypatch):
    monkeypatch.setattr(admin_service, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin_service, "_generate_channel_invite_code", lambda *_args, **_kwargs: "abcd1234abcd1234")
    channel = SimpleNamespace(
        id=1,
        channel_name="test_channel",
        invite_code="",
        sales_name="顾问A",
        status="ACTIVE",
        note="",
        created_at=datetime(2026, 5, 7, 10, 0, 0),
        users=[],
        admin_user_id=2,
    )
    advisor = SimpleNamespace(id=2, username="advisor")
    db = _FakeDbForUpdateChannelInviteCode(channel, advisor)
    current_admin = SimpleNamespace(id=10, username="admin", roles='["ADMIN"]')
    req = SimpleNamespace(model_dump=lambda **_kwargs: {})

    payload = await admin_service._update_channel(db, current_admin, 1, req)

    assert db.committed is True
    assert channel.invite_code == "abcd1234abcd1234"
    assert payload["invite_code"] == "abcd1234abcd1234"
