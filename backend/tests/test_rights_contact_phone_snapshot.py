from types import SimpleNamespace

from app.api.endpoints.loan import _extract_product_contact_phone
from app.services.loan_amounts import serialize_loan_snapshot


def test_extract_product_contact_phone_should_read_rights_detail_json():
    product = SimpleNamespace(rights_detail_json='{"contact_phone": "18320140697"}')

    assert _extract_product_contact_phone(product) == "18320140697"


def test_serialize_loan_snapshot_should_include_rights_contact_phone():
    loan = SimpleNamespace(
        id=1,
        user_id=2,
        status="DISBURSED",
        credit_limit=1500,
        approved_credit_limit=1500,
        fee_rate=0.6,
        fee_amount=900,
        term_days=7,
        penalty_amount=0,
        repaid_amount=0,
        reduction_amount=0,
        rights_contact_phone="18320140697",
        created_at=None,
        disbursed_at=None,
    )

    payload = serialize_loan_snapshot(loan)

    assert payload["rights_contact_phone"] == "18320140697"
