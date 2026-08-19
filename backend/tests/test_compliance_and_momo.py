from types import SimpleNamespace

import pytest

from app.services.compliance import calculate_effective_apr
from app.services.momo import complete_momo_transaction


def test_effective_apr_uses_actual_disbursement_amount():
    # 1000 principal, 40% upfront fee, 7 days: 400/600 annualized by 365/7.
    assert calculate_effective_apr(1000, 0.4, 7) == pytest.approx((400 / 600) * (365 / 7), rel=1e-6)


def test_complete_momo_transaction_is_idempotent_state_update():
    transaction = SimpleNamespace(
        status="PENDING",
        provider_reference=None,
        provider="mock",
        response_payload=None,
        failure_message=None,
        completed_at=None,
    )

    complete_momo_transaction(transaction, success=True, reference="MOCK-D-1", message="ok")

    assert transaction.status == "SUCCESS"
    assert transaction.provider_reference == "MOCK-D-1"
    assert transaction.failure_message is None
    assert transaction.completed_at is not None
