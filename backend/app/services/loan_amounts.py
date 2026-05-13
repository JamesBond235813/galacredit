from typing import Any, Optional


DEFAULT_FEE_RATE = 0.6
LOAN_PERIOD_DAYS = 7
MONTHLY_INTEREST_RATE = 0.02


def round_money(value: Any) -> float:
    return round(float(value or 0), 2)


def normalize_fee_rate(value: Any) -> float:
    if value is None:
        return DEFAULT_FEE_RATE

    rate = max(float(value), 0.0)
    return round(rate, 4)


def calculate_fee_amount(credit_limit: Any, fee_rate: Any) -> float:
    principal = round_money(credit_limit)
    rate = normalize_fee_rate(fee_rate)
    return round_money(principal * rate)


def calculate_interest_amount(credit_limit: Any, term_days: Any) -> float:
    principal = round_money(credit_limit)
    if not principal or term_days in (None, ""):
        return 0.0

    try:
        normalized_term_days = normalize_term_days(term_days)
    except ValueError:
        return 0.0

    return round_money(principal * MONTHLY_INTEREST_RATE * normalized_term_days / 30)


def calculate_guarantee_fee_amount(total_fee_amount: Any, credit_limit: Any, term_days: Any) -> float:
    total_fee = round_money(total_fee_amount)
    interest_amount = calculate_interest_amount(credit_limit, term_days)
    return round_money(max(total_fee - interest_amount, 0.0))


def calculate_total_repayment_by_values(
    credit_limit: Any,
    fee_rate: Any,
    penalty_amount: Any = 0,
) -> float:
    principal = round_money(credit_limit)
    fee_amount = calculate_fee_amount(principal, fee_rate)
    penalty = round_money(penalty_amount)
    return round_money(principal + fee_amount + penalty)


def normalize_term_days(term_days: Any, allow_empty: bool = False) -> Optional[int]:
    if term_days in (None, ""):
        if allow_empty:
            return None
        raise ValueError("请填写账期天数")

    try:
        numeric_term = float(term_days)
    except (TypeError, ValueError) as exc:
        raise ValueError("账期格式不正确") from exc

    if not numeric_term.is_integer():
        raise ValueError("期限必须为整数天")

    term = int(numeric_term)
    if term < 1:
        raise ValueError("期限不能少于1天")
    return term


def calculate_installment_periods(term_days: Any) -> int:
    normalize_term_days(term_days)
    return 1


def calculate_installment_by_values(
    credit_limit: Any,
    fee_rate: Any,
    term_days: Any,
) -> float:
    if not term_days:
        return 0.0

    try:
        periods = calculate_installment_periods(term_days)
    except (TypeError, ValueError):
        return 0.0

    principal = round_money(credit_limit)
    total_without_penalty = round_money(principal + calculate_fee_amount(principal, fee_rate))
    return round_money(total_without_penalty / periods)


def calculate_total_repayment_amount(loan: Any) -> float:
    return calculate_total_repayment_by_values(
        getattr(loan, "credit_limit", 0),
        getattr(loan, "fee_rate", DEFAULT_FEE_RATE),
        getattr(loan, "penalty_amount", 0),
    )


def calculate_installment_amount(loan: Any) -> float:
    return calculate_installment_by_values(
        getattr(loan, "credit_limit", 0),
        getattr(loan, "fee_rate", DEFAULT_FEE_RATE),
        getattr(loan, "term_days", None),
    )


def calculate_remaining_repayment_amount(loan: Any) -> float:
    total_amount = calculate_total_repayment_amount(loan)
    paid_and_reduced = round_money(getattr(loan, "repaid_amount", 0)) + round_money(
        getattr(loan, "reduction_amount", 0)
    )
    return round_money(max(total_amount - paid_and_reduced, 0.0))


def mask_secret(value: Any, left: int = 3, right: int = 2) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) <= left + right:
        return "*" * len(text)
    return f"{text[:left]}{'*' * (len(text) - left - right)}{text[-right:]}"


def sync_loan_fee_fields(loan: Any, fee_rate: Any = None):
    normalized_rate = normalize_fee_rate(
        fee_rate if fee_rate is not None else getattr(loan, "fee_rate", DEFAULT_FEE_RATE)
    )
    loan.fee_rate = normalized_rate
    loan.fee_amount = calculate_fee_amount(getattr(loan, "credit_limit", 0), normalized_rate)
    return loan


def serialize_loan_snapshot(loan: Any, include_user: bool = False, include_ledger: bool = False):
    credit_limit = getattr(loan, "credit_limit", 0)
    term_days = getattr(loan, "term_days", None)
    fee_rate = normalize_fee_rate(getattr(loan, "fee_rate", DEFAULT_FEE_RATE))
    fee_amount = calculate_fee_amount(credit_limit, fee_rate)
    interest_amount = calculate_interest_amount(credit_limit, term_days)
    guarantee_fee_amount = calculate_guarantee_fee_amount(fee_amount, credit_limit, term_days)

    review_admin = getattr(loan, "__dict__", {}).get("review_admin")
    collection_admin = getattr(loan, "__dict__", {}).get("collection_admin")

    payload = {
        "id": loan.id,
        "user_id": loan.user_id,
        "status": loan.status,
        "credit_limit": round_money(credit_limit),
        "approved_credit_limit": round_money(getattr(loan, "approved_credit_limit", 0) or credit_limit),
        "term_days": term_days,
        "due_date": getattr(loan, "due_date", None),
        "fee_rate": fee_rate,
        "fee_amount": fee_amount,
        "interest_amount": interest_amount,
        "guarantee_fee_amount": guarantee_fee_amount,
        "installment_amount": calculate_installment_by_values(
            credit_limit,
            fee_rate,
            term_days,
        ),
        "penalty_amount": round_money(getattr(loan, "penalty_amount", 0)),
        "repaid_amount": round_money(getattr(loan, "repaid_amount", 0)),
        "reduction_amount": round_money(getattr(loan, "reduction_amount", 0)),
        "total_repayment_amount": calculate_total_repayment_by_values(
            credit_limit,
            fee_rate,
            getattr(loan, "penalty_amount", 0),
        ),
        "remaining_repayment_amount": calculate_remaining_repayment_amount(loan),
        "review_note": getattr(loan, "review_note", None),
        "approved_at": getattr(loan, "approved_at", None),
        "reminder_count": getattr(loan, "reminder_count", 0) or 0,
        "last_reminded_at": getattr(loan, "last_reminded_at", None),
        "collection_count": getattr(loan, "collection_count", 0) or 0,
        "last_collection_at": getattr(loan, "last_collection_at", None),
        "collection_note": getattr(loan, "collection_note", None),
        "risk_report_checked_at": getattr(loan, "risk_report_checked_at", None),
        "risk_report_checked_by": getattr(loan, "risk_report_checked_by", None),
        "approval_discount_amount": round_money(getattr(loan, "approval_discount_amount", 0)),
        "order_discount_amount": round_money(getattr(loan, "order_discount_amount", 0)),
        "card_reissue_closed": bool(getattr(loan, "card_reissue_closed", False)),
        "extension_count": int(getattr(loan, "extension_count", 0) or 0),
        "extension_type": getattr(loan, "extension_type", None),
        "extension_note": getattr(loan, "extension_note", None),
        "overdue_hidden": bool(getattr(loan, "overdue_hidden", False)),
        "available_credit_limit": round_money(getattr(getattr(loan, "owner", None), "available_credit_limit", 0)),
        "overdue_credit_locked": bool(getattr(getattr(loan, "owner", None), "overdue_credit_locked", False)),
        "extension_source_loan_id": getattr(loan, "extension_source_loan_id", None),
        "extension_used_at": getattr(loan, "extension_used_at", None),
        "is_extension_fee_order": bool(getattr(loan, "is_extension_fee_order", False)),
        "identity_ocr_submitted_at": getattr(loan, "identity_ocr_submitted_at", None),
        "identity_face_auth_at": getattr(loan, "identity_face_auth_at", None),
        "fee_extension_ready": bool(getattr(loan, "fee_extension_ready", False)),
        "review_admin_id": getattr(loan, "review_admin_id", None),
        "review_admin_name": getattr(review_admin, "username", None),
        "collection_admin_id": getattr(loan, "collection_admin_id", None),
        "collection_admin_name": getattr(collection_admin, "username", None),
        "collection_transferred_at": getattr(loan, "collection_transferred_at", None),
        "repay_attempt_count": int(getattr(loan, "repay_attempt_count", 0) or 0),
        "product_id": getattr(loan, "product_id", None),
        "product_name": getattr(loan, "product_name", None),
        "rights_title": getattr(loan, "rights_title", None),
        "rights_desc": getattr(loan, "rights_desc", None),
        "rights_price": round_money(getattr(loan, "rights_price", 0)),
        "ecard_face_value": round_money(getattr(loan, "ecard_face_value", 0)),
        "product_total_price": round_money(
            getattr(loan, "product_total_price", 0)
            or round_money(
                round_money(getattr(loan, "ecard_face_value", 0) or credit_limit)
                + round_money(getattr(loan, "rights_price", 0) or fee_amount)
            )
        ),
        "product_term_days": getattr(loan, "product_term_days", None) or term_days,
        "ecard_account_masked": mask_secret(getattr(loan, "ecard_account", None), left=4, right=4) or None,
        "ecard_password_masked": mask_secret(getattr(loan, "ecard_password", None), left=4, right=4) or None,
        "ecard_expires_at": getattr(loan, "ecard_expires_at", None),
        "has_issued_ecard": bool(getattr(loan, "ecard_account", None) and getattr(loan, "ecard_password", None)),
        "relend_count": int(getattr(loan, "relend_count", 0) or 0),
        "relend_label": getattr(loan, "relend_label", None) or "初借",
        "created_at": getattr(loan, "created_at", None),
        "disbursed_at": getattr(loan, "disbursed_at", None),
    }

    latest_settled_loan = getattr(loan, "__dict__", {}).get("latest_settled_loan")
    if latest_settled_loan is not None:
        payload["latest_settled_loan"] = serialize_loan_snapshot(latest_settled_loan)

    if include_ledger:
        from app.services.loan_ledger import get_loan_ledger_snapshot

        ledger = get_loan_ledger_snapshot(loan)
        payload["installment_periods"] = ledger["summary"]["installment_periods"]
        payload["installments"] = ledger["installments"]
        payload["fund_flow_summary"] = ledger["summary"]

    if include_user:
        from app.services.upload_storage import build_upload_url

        owner = getattr(loan, "__dict__", {}).get("owner")
        source_channel = getattr(owner, "__dict__", {}).get("source_channel") if owner else None
        payload.update(
            {
                "user_phone": owner.phone if owner else "",
                "user_name": owner.name if owner else None,
                "user_id_card_num": owner.id_card_num if owner else None,
                "id_card_front_image_url": build_upload_url(getattr(owner, "id_card_front_image", None)) if owner else None,
                "id_card_back_image_url": build_upload_url(getattr(owner, "id_card_back_image", None)) if owner else None,
                "face_image_url": build_upload_url(getattr(owner, "face_image", None)) if owner else None,
                "user_face_auth_status": owner.face_auth_status if owner else None,
                "user_real_name_status": owner.real_name_status if owner else None,
                "user_blacklist_hit": bool(getattr(owner, "blacklist_hit", False)) if owner else False,
                "user_blacklist_reason": getattr(owner, "blacklist_reason", None) if owner else None,
                "user_source_channel_name": source_channel.channel_name if source_channel else None,
                "user_source_channel_sales_name": source_channel.sales_name if source_channel else None,
                "application_submitted_at": owner.application_submitted_at if owner else None,
                "last_login_at": owner.last_login_at if owner else None,
            }
        )

    return payload
