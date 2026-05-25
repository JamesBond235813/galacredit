from types import SimpleNamespace

import pytest

from app.services import admin_service


class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDb:
    def __init__(self, user):
        self._user = user
        self.committed = False

    async def execute(self, _stmt):
        return _FakeScalarResult(self._user)

    async def commit(self):
        self.committed = True


def test_serialize_user_summary_should_expose_location_risk_fields():
    user = SimpleNamespace(
        id=12,
        phone="18601143372",
        name="王辉",
        id_card_num="110101199001011234",
        id_card_front_image=None,
        id_card_back_image=None,
        face_image=None,
        face_auth_status="PASS",
        approved_limit=0,
        available_credit_limit=0,
        overdue_credit_locked=False,
        blacklist_hit=False,
        blacklist_reason=None,
        blacklist_checked_at=None,
        location_risk_blocked=True,
        location_risk_reason="登录位置异常：4小时内距离上次登录约52.5公里",
        location_risk_at="2026-05-22 16:13:13",
        risk_list_hit=False,
        risk_list_source=None,
        risk_list_reason=None,
        risk_list_checked_at=None,
        created_at="2026-05-22 10:00:00",
        last_login_at=None,
        application_submitted_at=None,
        source_channel=None,
        channel_bound_at=None,
        last_channel_visit_at=None,
        loans=[],
    )

    payload = admin_service.serialize_user_summary(user)

    assert payload["location_risk_blocked"] is True
    assert payload["location_risk_reason"] == "登录位置异常：4小时内距离上次登录约52.5公里"
    assert payload["location_risk_at"] == "2026-05-22 16:13:13"


@pytest.mark.asyncio
async def test_unlock_user_location_risk_should_only_clear_lock_fields(monkeypatch):
    events = []

    async def _fake_log_user_event_async(_db, **kwargs):
        events.append(kwargs)

    monkeypatch.setattr(admin_service, "log_user_event_async", _fake_log_user_event_async)

    user = SimpleNamespace(
        id=194,
        phone="18601143372",
        name="王辉",
        location_latitude="38.4080079",
        location_longitude="114.8064156",
        location_accuracy="48.46",
        location_address="河北省石家庄市",
        location_province="河北省",
        location_city="石家庄市",
        location_district="裕华区",
        location_street="裕华路",
        location_source="h5-login",
        location_updated_at="2026-05-22 13:31:48",
        location_risk_blocked=True,
        location_risk_reason="登录位置异常：4小时内距离上次登录约52.5公里",
        location_risk_at="2026-05-22 16:13:13",
    )
    db = _FakeDb(user)
    current_admin = SimpleNamespace(id=1, username="root", roles='["ADMIN"]', permissions=None)

    result = await admin_service._unlock_user_location_risk(db, current_admin, user_id=194)

    assert result == {"msg": "位置风控已解除"}
    assert db.committed is True
    assert user.location_risk_blocked is False
    assert user.location_risk_reason is None
    assert user.location_risk_at is None
    assert user.location_latitude == "38.4080079"
    assert user.location_longitude == "114.8064156"
    assert user.location_updated_at == "2026-05-22 13:31:48"
    assert events[0]["event_type"] == "ADMIN_LOCATION_RISK_UNLOCK"
