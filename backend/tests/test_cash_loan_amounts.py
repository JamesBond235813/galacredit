import json
from types import SimpleNamespace

from app.services.loan_amounts import (
    calculate_cash_loan_amounts,
    calculate_installment_amounts,
    normalize_installment_ratios,
)
from app.services.loan_ledger import build_installment_blueprint


def test_cash_loan_upfront_fee_mapping():
    result = calculate_cash_loan_amounts(1000, 0.4)
    assert result == {
        "nominal_loan_amount": 1000.0,
        "upfront_fee_amount": 400.0,
        "actual_disbursement_amount": 600.0,
        "total_repayment_amount": 1000.0,
    }


def test_installments_use_configured_ratios_and_last_period_carries_rounding():
    assert calculate_installment_amounts(1000, [0.6, 0.4], 2) == [600.0, 400.0]
    assert calculate_installment_amounts(100, [1, 1, 1], 3) == [33.33, 33.33, 33.34]
    assert normalize_installment_ratios(json.dumps([6, 4]), 2) == [0.6, 0.4]


def test_cash_loan_installment_blueprint_uses_nominal_repayment_total():
    loan = SimpleNamespace(
        term_days=7,
        disbursed_at=__import__("datetime").datetime(2026, 8, 18),
        due_date=__import__("datetime").datetime(2026, 8, 25),
        installment_count=2,
        installment_ratios_json=json.dumps([0.6, 0.4]),
        total_repayment_amount_snapshot=1000,
    )
    items = build_installment_blueprint(loan)
    assert [item["due_amount"] for item in items] == [600.0, 400.0]
    assert items[-1]["due_date"] == loan.due_date
