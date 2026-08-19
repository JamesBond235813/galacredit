import pytest
from pydantic import ValidationError

from app.schemas.user import ApplicationSubmitRequest, EmergencyContactRequest


def test_emergency_contact_accepts_ghana_international_phone():
    request = EmergencyContactRequest(name="Ama Mensah", relation="Parents", phone="233240000001", source="CONTACT_PICKER", category="FAMILY")

    assert request.phone == "233240000001"


def test_emergency_contact_keeps_legacy_phone_compatibility():
    request = EmergencyContactRequest(name="Legacy Contact", relation="Friends", phone="13800000000", source="CONTACT_PICKER", category="SOCIAL")

    assert request.phone == "13800000000"


@pytest.mark.parametrize("phone", ["0240000001", "2332400000019", "+233240000001"])
def test_emergency_contact_rejects_noncanonical_phone(phone):
    with pytest.raises(ValidationError):
        EmergencyContactRequest(name="Ama Mensah", relation="Parents", phone=phone, source="CONTACT_PICKER", category="FAMILY")


def test_emergency_contact_rejects_manual_source():
    with pytest.raises(ValidationError):
        EmergencyContactRequest(name="Ama Mensah", relation="Parents", phone="233240000001", source="MANUAL", category="FAMILY")


def test_application_requires_family_then_social_contact():
    request = ApplicationSubmitRequest(
        emergency_contacts=[
            EmergencyContactRequest(name="Family", relation="Brothers or sisters", phone="233240000001", source="CONTACT_PICKER", category="FAMILY"),
            EmergencyContactRequest(name="Friend", relation="Classmates", phone="233250000001", source="CONTACT_PICKER", category="SOCIAL"),
        ]
    )

    assert request.emergency_contacts[0].category == "FAMILY"
    assert request.emergency_contacts[1].category == "SOCIAL"


def test_application_rejects_social_relation_for_first_contact():
    with pytest.raises(ValidationError, match="contact 1 must be a family member"):
        ApplicationSubmitRequest(
            emergency_contacts=[
                EmergencyContactRequest(name="Wrong", relation="Friends", phone="233240000001", source="CONTACT_PICKER", category="FAMILY"),
                EmergencyContactRequest(name="Friend", relation="Colleagues", phone="233250000001", source="CONTACT_PICKER", category="SOCIAL"),
            ]
        )
