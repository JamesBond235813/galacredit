import pytest

from types import SimpleNamespace

from app.schemas.channel import ChannelCreateRequest, ChannelUpdateRequest
from app.schemas.loan import ProductCreateRequest
from app.api.endpoints.user import apply_auto_review_product
from app.services.compliance import validate_cash_loan_fee_components
from app.services.loan_flow import resolve_borrower_type


def test_cash_loan_fee_components_must_match_total_rate():
    components = {
        "system_service_fee_rate": 0.10,
        "control_fee_rate": 0.10,
        "channel_fee_rate": 0.05,
        "interest_rate": 0.15,
    }
    assert validate_cash_loan_fee_components(0.40, components) == components

    with pytest.raises(Exception, match="之和必须等于"):
        validate_cash_loan_fee_components(0.35, components)


def test_product_policy_accepts_new_and_repeat_borrower_types():
    request = ProductCreateRequest(
        name="New policy",
        ecard_face_value=0,
        rights_price=0,
        rights_title="GalaCredit cash loan",
        term_days=7,
        repayment_due_day=7,
        nominal_loan_amount=1000,
        payment_amount=1000,
        upfront_fee_rate=0.4,
        fee_components={
            "system_service_fee_rate": 0.1,
            "control_fee_rate": 0.1,
            "channel_fee_rate": 0.05,
            "interest_rate": 0.15,
        },
        borrower_type="NEW",
    )
    assert request.borrower_type == "NEW"


def test_channel_has_independent_review_and_disbursement_modes():
    request = ChannelCreateRequest(
        channel_name="ghana_test",
        sales_name="Advisor",
        admin_user_id=1,
        review_mode="AUTO_REVIEW",
        disbursement_mode="MANUAL_DISBURSE",
    )
    assert request.review_mode == "AUTO_REVIEW"
    assert request.disbursement_mode == "MANUAL_DISBURSE"
    assert ChannelUpdateRequest(review_mode="MANUAL_REVIEW").review_mode == "MANUAL_REVIEW"


def test_borrower_type_is_new_until_a_settled_loan_exists():
    assert resolve_borrower_type([]) == "NEW"
    assert resolve_borrower_type([type("Loan", (), {"id": 1, "status": "REVIEWING"})()]) == "NEW"
    assert resolve_borrower_type([type("Loan", (), {"id": 1, "status": "SETTLED"})()]) == "REPEAT"


def test_auto_review_applies_cash_loan_snapshot_for_follow_up_order_flow():
    loan = SimpleNamespace()
    user = SimpleNamespace(approved_limit=0, available_credit_limit=0)
    product = SimpleNamespace(
        id=9,
        name="GalaCredit New Borrower 7-Day",
        product_type="CASH_LOAN",
        nominal_loan_amount=1000,
        payment_amount=1000,
        upfront_fee_rate=0.4,
        term_days=7,
        interest_start_day=1,
        repayment_due_day=7,
        installment_count=2,
        installment_ratios_json="[0.6,0.4]",
        fee_components_json='{"system_service_fee_rate":0.1}',
        daily_overdue_fee=10,
    )

    assert apply_auto_review_product(loan, user, product) == 1000
    assert loan.status == "APPROVED"
    assert loan.actual_disbursement_amount == 600
    assert loan.total_repayment_amount_snapshot == 1000
    assert loan.product_id == 9
    assert loan.installment_count == 2
    assert loan.daily_overdue_fee_snapshot == 10
    assert user.available_credit_limit == 1000
