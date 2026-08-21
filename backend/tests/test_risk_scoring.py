import pytest

from app.services.risk_scoring import calculate_rule_scores
from app.services.risk_external import ExternalRiskResult, combine_external_score


def test_rule_score_blocks_blacklisted_user():
    result = calculate_rule_scores(identity_verified=True, face_verified=True, blacklist_hit=True)
    assert result.decision == "BLOCK"
    assert "BLACKLIST_HIT" in result.reasons


def test_rule_score_refers_high_velocity_or_wallet_mismatch():
    result = calculate_rule_scores(identity_verified=True, face_verified=True, blacklist_hit=False,
                                   application_count_24h=6, wallet_match=False)
    assert result.decision == "REFER"
    assert result.recommended_limit == 500.0


def test_rule_score_approves_verified_low_risk_user():
    result = calculate_rule_scores(identity_verified=True, face_verified=True, blacklist_hit=False)
    assert result.decision == "APPROVE"
    assert result.recommended_limit == 1000.0


def test_external_provider_failure_keeps_internal_score():
    base = calculate_rule_scores(identity_verified=True, face_verified=True, blacklist_hit=False)
    result = combine_external_score(base, ExternalRiskResult("NIA", "FAILED", 99, "timeout", {}))
    assert result == base


def test_external_success_is_explicitly_recorded_in_reasons():
    base = calculate_rule_scores(identity_verified=True, face_verified=True, blacklist_hit=False)
    result = combine_external_score(base, ExternalRiskResult("BUREAU", "SUCCESS", 60, "ok", {}))
    assert "EXTERNAL_SCORE_USED" in result.reasons
