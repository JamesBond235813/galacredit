from types import SimpleNamespace

from app.services.risk_policy import (
    build_default_risk_policy_config,
    calculate_risk_policy_rollout_bucket,
    is_risk_policy_in_rollout,
    normalize_risk_policy_config,
    serialize_risk_policy_version,
)


def test_normalize_risk_policy_config_should_fill_default_sections():
    """策略配置缺省时应自动补齐默认结构。

    :return: 无返回值
    """
    config = normalize_risk_policy_config({"policy_name": "Demo"})

    assert config["policy_name"] == "Demo"
    assert config["mode"] == "SHADOW"
    assert config["decision_thresholds"]["block_score"] == 80
    assert config["rule_points"]["BLACKLIST_HIT"] == 100


def test_serialize_risk_policy_version_should_expose_summary_fields():
    """策略版本序列化应返回摘要字段与激活状态。

    :return: 无返回值
    """
    row = SimpleNamespace(
        id=1,
        policy_key="GHANA_CASH_LOAN_BASELINE",
        version_no=3,
        status="ACTIVE",
        rollout_percent=25,
        config_json=build_default_risk_policy_config(),
        created_by="tester",
        created_at="2026-08-21 20:00:00",
    )

    payload = serialize_risk_policy_version(row)

    assert payload["version_no"] == 3
    assert payload["status"] == "ACTIVE"
    assert payload["is_active"] is True
    assert payload["config_summary"]["mode"] == "SHADOW"


def test_rollout_bucket_should_be_stable_and_bounded():
    """灰度分桶值应稳定且落在 0 到 99 之间。

    :return: 无返回值
    """
    bucket_a = calculate_risk_policy_rollout_bucket(
        policy_key="GHANA_CASH_LOAN_BASELINE",
        version_no=3,
        subject_id=1001,
    )
    bucket_b = calculate_risk_policy_rollout_bucket(
        policy_key="GHANA_CASH_LOAN_BASELINE",
        version_no=3,
        subject_id=1001,
    )
    bucket_c = calculate_risk_policy_rollout_bucket(
        policy_key="GHANA_CASH_LOAN_BASELINE",
        version_no=3,
        subject_id=1002,
    )

    assert bucket_a == bucket_b
    assert 0 <= bucket_a < 100
    assert bucket_a != bucket_c


def test_rollout_gate_should_match_percent_threshold():
    """灰度开关应按比例判断命中范围。

    :return: 无返回值
    """
    assert is_risk_policy_in_rollout(
        policy_key="GHANA_CASH_LOAN_BASELINE",
        version_no=3,
        rollout_percent=100,
        subject_id=1001,
    ) is True
    assert is_risk_policy_in_rollout(
        policy_key="GHANA_CASH_LOAN_BASELINE",
        version_no=3,
        rollout_percent=0,
        subject_id=1001,
    ) is False
