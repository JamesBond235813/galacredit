from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.user import UserDetailResponse
from app.services import admin_service


def test_serialize_user_summary_should_mask_phone_and_id_card(monkeypatch):
    monkeypatch.setattr(admin_service, "get_relend_count", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(admin_service, "get_relend_label", lambda *_args, **_kwargs: "初借")
    monkeypatch.setattr(admin_service, "get_latest_normal_settled_loan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        admin_service,
        "serialize_loan_snapshot",
        lambda *_args, **_kwargs: {
            "credit_limit": None,
            "term_days": None,
            "due_date": None,
            "fee_rate": None,
            "fee_amount": None,
            "interest_amount": None,
            "guarantee_fee_amount": None,
            "penalty_amount": None,
        },
    )
    user = SimpleNamespace(
        id=1,
        phone="13812345678",
        name="测试用户",
        id_card_num="330301199901011234",
        face_auth_status="PASS",
        approved_limit=1000,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
        application_submitted_at=None,
        source_channel=SimpleNamespace(channel_name="ch1", sales_name="sale1"),
        channel_bound_at=None,
        last_channel_visit_at=None,
        loans=[
            SimpleNamespace(id=2, status="DISBURSED", disbursed_at=datetime(2026, 1, 3, 10, 0, 0), product_total_price=1888),
            SimpleNamespace(id=9, status="SETTLED", disbursed_at=datetime(2026, 2, 3, 11, 0, 0), product_total_price=2888),
            SimpleNamespace(id=12, status="REVIEWING", disbursed_at=None, product_total_price=3888),
        ],
    )

    payload = admin_service.serialize_user_summary(user)

    assert payload["phone"] == "*******5678"
    assert payload["id_card_num"] == "330301***********4"
    assert payload["first_disbursed_at"] == datetime(2026, 1, 3, 10, 0, 0)
    assert payload["first_deal_amount"] == 1888
    assert payload["latest_disbursed_at"] == datetime(2026, 2, 3, 11, 0, 0)
    assert payload["latest_deal_amount"] == 2888


def test_serialize_user_detail_should_include_first_deal_loan():
    loan_1 = SimpleNamespace(
        id=1,
        user_id=1,
        status="REJECTED",
        created_at=datetime(2026, 1, 1),
        disbursed_at=None,
        credit_limit=1000,
        fee_rate=0.6,
        fee_amount=100,
        interest_amount=0,
        guarantee_fee_amount=0,
        installment_amount=0,
        term_days=7,
        due_date=None,
        penalty_amount=0,
        repaid_amount=0,
        reduction_amount=0,
        review_note="",
        approved_at=None,
        reminder_count=0,
        last_reminded_at=None,
        collection_count=0,
        last_collection_at=None,
        collection_note=None,
        relend_count=0,
        relend_label="初借",
        latest_settled_loan=None,
        installments=[],
        transactions=[],
        owner=SimpleNamespace(loans=[]),
        product_total_price=0,
        rights_price=0,
        ecard_face_value=0,
    )
    loan_2 = SimpleNamespace(
        id=2,
        user_id=1,
        status="DISBURSED",
        created_at=datetime(2026, 1, 2),
        disbursed_at=datetime(2026, 1, 3, 10, 0, 0),
        credit_limit=2000,
        fee_rate=0.6,
        fee_amount=120,
        interest_amount=0,
        guarantee_fee_amount=0,
        installment_amount=0,
        term_days=14,
        due_date=None,
        penalty_amount=0,
        repaid_amount=0,
        reduction_amount=0,
        review_note="",
        approved_at=None,
        reminder_count=0,
        last_reminded_at=None,
        collection_count=0,
        last_collection_at=None,
        collection_note=None,
        relend_count=0,
        relend_label="初借",
        latest_settled_loan=None,
        installments=[],
        transactions=[],
        owner=SimpleNamespace(loans=[]),
        product_total_price=0,
        rights_price=0,
        ecard_face_value=0,
    )
    user = SimpleNamespace(
        id=1,
        phone="13812345678",
        name="测试",
        id_card_num="330301199901011234",
        id_address=None,
        id_expiry=None,
        approved_limit=1000,
        emergency_contact1_name=None,
        emergency_contact1_relation=None,
        emergency_contact1_phone=None,
        emergency_contact2_name=None,
        emergency_contact2_relation=None,
        emergency_contact2_phone=None,
        location_latitude=None,
        location_longitude=None,
        location_accuracy=None,
        location_address=None,
        location_province=None,
        location_city=None,
        location_district=None,
        location_street=None,
        location_source=None,
        location_updated_at=None,
        face_auth_status="PASS",
        face_auth_at=None,
        last_login_at=None,
        ocr_submitted_at=None,
        application_submitted_at=None,
        source_channel=SimpleNamespace(channel_name="ch1", sales_name="sale1"),
        channel_bound_at=None,
        last_channel_visit_at=None,
        created_at=datetime(2026, 1, 1),
        loans=[loan_1, loan_2],
    )

    payload = admin_service.serialize_user_detail(user, events=[])

    assert payload["first_deal_loan"]["id"] == 2
    assert payload["first_deal_loan"]["status"] == "DISBURSED"


def test_serialize_user_detail_should_normalize_empty_event_location_fields():
    user = SimpleNamespace(
        id=1,
        phone="13812345678",
        name="测试",
        id_card_num="330301199901011234",
        id_address=None,
        id_expiry=None,
        approved_limit=1000,
        emergency_contact1_name=None,
        emergency_contact1_relation=None,
        emergency_contact1_phone=None,
        emergency_contact2_name=None,
        emergency_contact2_relation=None,
        emergency_contact2_phone=None,
        location_latitude=None,
        location_longitude=None,
        location_accuracy=None,
        location_address=None,
        location_province=None,
        location_city=None,
        location_district=None,
        location_street=None,
        location_source=None,
        location_updated_at=None,
        face_auth_status="PASS",
        face_auth_at=None,
        last_login_at=None,
        ocr_submitted_at=None,
        application_submitted_at=None,
        source_channel=None,
        channel_bound_at=None,
        last_channel_visit_at=None,
        created_at=datetime(2026, 1, 1),
        loans=[],
    )
    event = SimpleNamespace(
        id=1,
        loan_id=None,
        actor_type="USER",
        operator_name=None,
        event_type="LOCATION_REPARSE",
        title="GPS解析",
        detail=None,
        ip=None,
        ip_country=None,
        ip_province=None,
        ip_city=None,
        ip_district=None,
        ip_detail=None,
        lon_lat=None,
        lon_lat_province=None,
        lon_lat_city=None,
        lon_lat_district=None,
        lon_lat_detail=None,
        created_at=datetime(2026, 6, 1, 10, 32, 0),
    )

    payload = admin_service.serialize_user_detail(user, events=[event])
    response = UserDetailResponse.model_validate(payload)

    assert response.events[0].ip_detail == ""
    assert response.events[0].lon_lat_detail == ""


def test_apply_business_consultant_user_summary_status_should_set_first_borrow_for_only_consultant():
    current_admin = SimpleNamespace(id=9, username="advisor", roles='["BUSINESS_CONSULTANT"]')
    user_summary = {
        "current_loan_status": "REVIEWING",
        "first_disbursed_at": datetime(2026, 4, 1, 10, 0, 0),
    }

    payload = admin_service.apply_business_consultant_user_summary_status(user_summary, current_admin)

    assert payload["current_loan_status"] == "FIRST_BORROW"


def test_apply_business_consultant_user_summary_status_should_not_change_for_mixed_roles():
    current_admin = SimpleNamespace(id=9, username="advisor", roles='["BUSINESS_CONSULTANT", "REVIEW"]')
    user_summary = {
        "current_loan_status": "REVIEWING",
        "first_disbursed_at": datetime(2026, 4, 1, 10, 0, 0),
    }

    payload = admin_service.apply_business_consultant_user_summary_status(user_summary, current_admin)

    assert payload["current_loan_status"] == "REVIEWING"


@pytest.mark.asyncio
async def test_reset_user_password_should_forbid_business_consultant(monkeypatch):
    current_admin = SimpleNamespace(id=9, username="advisor", roles='["BUSINESS_CONSULTANT"]')

    monkeypatch.setattr(admin_service, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)

    with pytest.raises(HTTPException) as exc_info:
        await admin_service._reset_user_password(
            db=SimpleNamespace(),
            current_admin=current_admin,
            user_id=1,
            req=SimpleNamespace(password="123456"),
        )

    assert exc_info.value.status_code == 403


class _ScalarsResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


class _FakeDbForSourceChannels:
    def __init__(self, channels):
        self._channels = channels

    async def execute(self, _stmt):
        return _ScalarsResult(self._channels)


@pytest.mark.asyncio
async def test_get_user_source_channels_should_return_serialized_channels(monkeypatch):
    monkeypatch.setattr(admin_service, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)
    db = _FakeDbForSourceChannels(
        [
            SimpleNamespace(id=11, channel_name="a", sales_name="A", status="ACTIVE"),
            SimpleNamespace(id=12, channel_name="b", sales_name="B", status="ACTIVE"),
        ]
    )
    current_admin = SimpleNamespace(id=99, username="advisor", roles='["BUSINESS_CONSULTANT"]')

    result = await admin_service._get_user_source_channels(db, current_admin, keyword="", limit=50)

    assert result == [
        {"id": 11, "channel_name": "a", "sales_name": "A", "status": "ACTIVE"},
        {"id": 12, "channel_name": "b", "sales_name": "B", "status": "ACTIVE"},
    ]
