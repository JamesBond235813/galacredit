import asyncio
from types import SimpleNamespace

from app.services import login_location_risk


class _FakeDb:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        return None


def _build_user():
    return SimpleNamespace(
        id=1,
        location_latitude=None,
        location_longitude=None,
        location_accuracy=None,
        location_address="旧地址",
        location_province="旧省",
        location_city="旧市",
        location_district="旧区",
        location_street="旧街道",
        location_source=None,
        location_updated_at=None,
        location_risk_blocked=False,
        location_risk_reason=None,
        location_risk_at=None,
    )


def test_apply_login_location_should_not_fallback_ip_as_gps_address(monkeypatch):
    async def _empty_reverse_geocode(**_kwargs):
        return {
            "address": None,
            "province": None,
            "city": None,
            "district": None,
            "street": None,
        }

    async def _noop_log(*_args, **_kwargs):
        return None

    monkeypatch.setattr(login_location_risk, "reverse_geocode", _empty_reverse_geocode)
    monkeypatch.setattr(login_location_risk, "log_user_event_async", _noop_log)
    db = _FakeDb()
    user = _build_user()

    asyncio.run(
        login_location_risk.apply_login_location(
            db,
            user,
            latitude=36.733636,
            longitude=101.752695,
            accuracy=12.4,
            fallback_ip="36.21.252.191",
        )
    )

    assert user.location_latitude == "36.733636"
    assert user.location_longitude == "101.752695"
    assert user.location_province is None
    assert user.location_city is None
    assert user.location_address is None
