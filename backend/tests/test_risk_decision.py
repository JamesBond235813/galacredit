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


def test_baseline_rule_can_disable_blacklist_hit_by_policy_config():
    result = evaluate_baseline_rules(
        _user(blacklist_hit=True),
        None,
        "APPLICATION",
        policy_config={
            "rule_enables": {
                "BLACKLIST_HIT": False,
            }
        },
    )
    assert result.decision == "APPROVE"
    assert result.reasons == ()


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


def test_record_risk_decision_should_resolve_gray_mode_by_policy_rollout(monkeypatch):
    """命中灰度时应把执行模式记录为 ENFORCE。

    :return: 无返回值
    """
    from app import services as services_pkg
    from app.services import risk_decision as risk_decision_module

    class FakeDb:
        def __init__(self):
            self.items = []

        def add(self, item):
            self.items.append(item)

        async def flush(self):
            self.items[0].id = 1

        async def execute(self, *args, **kwargs):
            return None

    active_policy = SimpleNamespace(
        policy_key="GHANA_CASH_LOAN_BASELINE",
        version_no=4,
        status="ACTIVE",
        rollout_percent=100,
        config_json={"mode": "ENFORCE"},
    )

    async def fake_get_active_risk_policy_version(*args, **kwargs):
        return active_policy

    monkeypatch.setattr(risk_decision_module, "get_active_risk_policy_version", fake_get_active_risk_policy_version)

    db = FakeDb()
    record = asyncio.run(record_risk_decision_async(db, user=_user(), loan=None, stage="APPLICATION"))

    assert record.mode == "ENFORCE"
    assert record.feature_snapshot_json
    assert db.items[0].mode == "ENFORCE"
