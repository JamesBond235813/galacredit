from types import SimpleNamespace
import asyncio

from app.services.risk_decision import evaluate_baseline_rules, record_risk_decision_async


def _user(**kwargs):
    values = {
        "id": 1,
        "phone": "233240000000",
        "real_name_status": "VERIFIED",
        "face_auth_status": "PASSED",
        "blacklist_hit": False,
        "risk_list_hit": False,
        "location_risk_blocked": False,
        "overdue_credit_locked": False,
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_baseline_rule_returns_approve_for_verified_clean_user():
    result = evaluate_baseline_rules(_user(), None, "APPLICATION")
    assert result.decision == "APPROVE"
    assert result.score == 0
    assert result.reasons == ()


def test_baseline_rule_blocks_blacklist_and_external_risk_hit():
    result = evaluate_baseline_rules(_user(blacklist_hit=True, risk_list_hit=True), None, "APPLICATION")
    assert result.decision == "BLOCK"
    assert set(result.reasons) == {"BLACKLIST_HIT", "EXTERNAL_RISK_LIST_HIT"}
    assert result.score == 100


def test_baseline_rule_refers_incomplete_kyc_and_overdue_credit():
    loan = SimpleNamespace(status="OVERDUE")
    result = evaluate_baseline_rules(
        _user(real_name_status="UNVERIFIED", face_auth_status="PENDING", overdue_credit_locked=True),
        loan,
        "ORDER",
    )
    assert result.decision == "REFER"
    assert "IDENTITY_NOT_VERIFIED" in result.reasons
    assert "FACE_NOT_VERIFIED" in result.reasons
    assert "CURRENT_LOAN_OVERDUE" in result.reasons
    assert "OVERDUE_CREDIT_LOCKED" in result.reasons


def test_baseline_rule_declines_missing_phone_without_user_data_translation():
    result = evaluate_baseline_rules(_user(phone=None), None, "APPLICATION")
    assert result.decision == "DECLINE"
    assert "PHONE_MISSING" in result.reasons


def test_record_risk_decision_writes_decision_and_rule_hits_without_commit():
    class FakeDb:
        def __init__(self):
            self.items = []

        def add(self, item):
            self.items.append(item)

        async def flush(self):
            self.items[0].id = 1

    db = FakeDb()
    record = asyncio.run(record_risk_decision_async(db, user=_user(blacklist_hit=True), loan=None, stage="APPLICATION"))
    assert record.id == 1
    assert record.decision == "BLOCK"
    assert record.mode == "SHADOW"
    assert len(db.items) == 2
    assert db.items[1].rule_code == "BLACKLIST_HIT"
