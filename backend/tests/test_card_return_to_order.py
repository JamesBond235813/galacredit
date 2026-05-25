from datetime import datetime
from types import SimpleNamespace

from app.services.admin_service import _return_loan_to_approved_for_reorder


def test_return_card_order_to_approved_should_clear_order_and_restore_credit():
    """退回待下单应撤销本次下单并恢复可用额度。

    :return: 无返回值
    """
    owner = SimpleNamespace(approved_limit=0, available_credit_limit=0, overdue_credit_locked=True)
    loan = SimpleNamespace(
        owner=owner,
        status="CARD_REJECTED",
        card_reissue_closed=True,
        credit_limit=1000,
        approved_credit_limit=4800,
        fee_rate=0.6,
        fee_amount=600,
        order_discount_amount=0,
        due_date=datetime.now(),
        disbursed_at=datetime.now(),
        penalty_amount=10,
        repaid_amount=20,
        reduction_amount=30,
        paid_penalty_amount=1,
        reduced_penalty_amount=2,
        reminder_count=3,
        last_reminded_at=datetime.now(),
        collection_count=4,
        last_collection_at=datetime.now(),
        collection_note="note",
        collection_admin_id=8,
        collection_transferred_at=datetime.now(),
        repay_attempt_count=5,
        product_id=1,
        product_name="错误商品",
        rights_title="权益",
        rights_desc="描述",
        rights_contact_phone="18320140697",
        rights_price=600,
        ecard_face_value=1000,
        product_total_price=1600,
        product_term_days=7,
        term_days=7,
        ecard_account="card",
        ecard_password="pwd",
        ecard_expires_at=datetime.now(),
        order_no="XHB202605210001",
    )

    restored_credit = _return_loan_to_approved_for_reorder(loan)

    assert restored_credit == 4800
    assert loan.status == "APPROVED"
    assert loan.credit_limit == 4800
    assert loan.product_id is None
    assert loan.product_name is None
    assert loan.product_total_price == 0
    assert loan.ecard_face_value == 0
    assert loan.order_no == ""
    assert owner.approved_limit == 4800
    assert owner.available_credit_limit == 4800
    assert owner.overdue_credit_locked is False
