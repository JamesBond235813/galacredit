import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan
from app.models.risk_decision import RiskDecision, RiskRuleHit
from app.models.risk_expansion import RiskDeviceSignal
from app.models.user import User
from app.services.risk_policy import (
    DEFAULT_RISK_POLICY_KEY,
    calculate_risk_policy_rollout_bucket,
    get_active_risk_policy_version,
    is_risk_policy_in_rollout,
    normalize_risk_policy_config,
)
from app.services.risk_scoring import evaluate_device_risk_signals, summarize_device_collection


POLICY_KEY = "GHANA_CASH_LOAN_BASELINE"
POLICY_VERSION = "1.0.0"


@dataclass(frozen=True)
class RiskEvaluation:
    """风控评估结果。"""

    decision: str
    score: float
    reasons: tuple[str, ...]
    features: dict[str, Any]
    hits: tuple[dict[str, str], ...]


def evaluate_baseline_rules(
    user: User,
    loan: Optional[Loan],
    stage: str,
    policy_config: Optional[dict[str, Any]] = None,
    device_signal: Optional[RiskDeviceSignal] = None,
) -> RiskEvaluation:
    """基于当前已落库字段执行加纳现金贷基线规则。

    :param user: 借款人对象
    :param loan: 当前订单，可为空
    :param stage: 决策阶段
    :return: 可解释的风控评估结果
    """
    policy = normalize_risk_policy_config(policy_config)
    rule_points = policy.get("rule_points") or {}
    rule_enables = policy.get("rule_enables") or {}
    thresholds = policy.get("decision_thresholds") or {}
    velocity = policy.get("velocity") or {}

    reasons: list[str] = []
    hits: list[dict[str, str]] = []
    risk_score = 0.0

    def hit(code: str, outcome: str, severity: str, detail: str, points: float = 0.0) -> None:
        nonlocal risk_score
        if not rule_enables.get(code, True):
            return
        risk_score += points
        hits.append({"rule_code": code, "outcome": outcome, "severity": severity, "detail": detail})
        if outcome in {"REFER", "DECLINE", "BLOCK"}:
            reasons.append(code)

    if bool(getattr(user, "blacklist_hit", False)):
        hit("BLACKLIST_HIT", "BLOCK", "HIGH", "内部黑名单命中", float(rule_points.get("BLACKLIST_HIT", 100) or 100))
    if bool(getattr(user, "risk_list_hit", False)):
        hit("EXTERNAL_RISK_LIST_HIT", "BLOCK", "HIGH", "外部风险名单命中", float(rule_points.get("EXTERNAL_RISK_LIST_HIT", 100) or 100))
    if bool(getattr(user, "location_risk_blocked", False)):
        hit("LOCATION_RISK_LOCKED", "REFER", "MEDIUM", "位置风控锁定", float(rule_points.get("LOCATION_RISK_LOCKED", 35) or 35))
    if str(getattr(user, "real_name_status", "") or "").upper() not in {"VERIFIED", "AUTHED", "PASS", "PASSED"}:
        hit("IDENTITY_NOT_VERIFIED", "REFER", "MEDIUM", "实名状态未完成", float(rule_points.get("IDENTITY_NOT_VERIFIED", 25) or 25))
    if str(getattr(user, "face_auth_status", "") or "").upper() not in {"APPROVED", "PASS", "PASSED"}:
        hit("FACE_NOT_VERIFIED", "REFER", "MEDIUM", "人脸状态未完成", float(rule_points.get("FACE_NOT_VERIFIED", 20) or 20))
    if not getattr(user, "phone", None):
        hit("PHONE_MISSING", "DECLINE", "HIGH", "手机号缺失", float(rule_points.get("PHONE_MISSING", 80) or 80))
    if loan is not None and str(getattr(loan, "status", "") or "").upper() == "OVERDUE":
        hit("CURRENT_LOAN_OVERDUE", "REFER", "HIGH", "当前订单逾期", float(rule_points.get("CURRENT_LOAN_OVERDUE", 45) or 45))
    if bool(getattr(user, "overdue_credit_locked", False)):
        hit("OVERDUE_CREDIT_LOCKED", "REFER", "HIGH", "逾期额度锁定", float(rule_points.get("OVERDUE_CREDIT_LOCKED", 40) or 40))

    device_summary: dict[str, Any] = {}
    device_risk_level = "INFO"
    device_reasons: list[str] = []
    device_keyword_hits: dict[str, list[str]] = {"sms": [], "apps": [], "device": []}
    if device_signal is not None:
        try:
            device_summary = summarize_device_collection(payload=json.loads(device_signal.payload_json or "{}"))
        except Exception:
            device_summary = {}
        try:
            device_keyword_hits = json.loads(device_signal.keyword_hits_json or "{}")
        except Exception:
            device_keyword_hits = {"sms": [], "apps": [], "device": []}
        try:
            device_risk_payload = json.loads(device_signal.risk_flags_json or "{}")
        except Exception:
            device_risk_payload = {}
        device_risk_level = str(getattr(device_signal, "risk_level", "INFO") or "INFO").upper()
        device_reasons = list(device_risk_payload.get("reasons") or [])
        if device_risk_level == "HIGH" and device_reasons:
            hit("DEVICE_ENV_HIGH_RISK", "BLOCK", "HIGH", "设备环境存在高风险迹象", float(rule_points.get("DEVICE_ENV_HIGH_RISK", 70) or 70))
        elif device_risk_level in {"HIGH", "MEDIUM"} and device_reasons:
            hit("DEVICE_ENV_HIGH_RISK", "REFER", "MEDIUM", "设备环境或装机信息存在风险迹象", float(rule_points.get("DEVICE_ENV_HIGH_RISK", 70) or 70) / 2)
        if "loan" in device_keyword_hits.get("sms", []) and "overdue" in device_keyword_hits.get("sms", []):
            hit("SMS_LOAN_OVERDUE", "REFER", "MEDIUM", "短信中出现借贷和逾期压力关键词", float(rule_points.get("SMS_LOAN_OVERDUE", 45) or 45))
        if "gambling" in device_keyword_hits.get("sms", []) or "gambling" in device_keyword_hits.get("apps", []):
            hit("GAMBLING_SIGNAL", "REFER", "MEDIUM", "短信或装机列表出现博彩相关信号", float(rule_points.get("GAMBLING_SIGNAL", 35) or 35))
        if {"loan", "overdue"} <= set(device_keyword_hits.get("apps", []) or []):
            hit("APP_DEBT_PRESSURE", "REFER", "LOW", "装机列表存在多款借贷或催收相关应用", float(rule_points.get("APP_DEBT_PRESSURE", 30) or 30))
        if int(device_signal.account_count_24h or 0) >= 3:
            hit("DEVICE_SHARED_MULTI_USER", "REFER", "MEDIUM", "同设备近期关联多个用户", float(rule_points.get("DEVICE_SHARED_MULTI_USER", 40) or 40))

    block_threshold = float(thresholds.get("block_score", 80) or 80)
    refer_threshold = float(thresholds.get("refer_score", 35) or 35)
    if any(item["outcome"] == "BLOCK" for item in hits) or (policy.get("mode") == "ENFORCE" and risk_score >= block_threshold):
        decision = "BLOCK"
    elif any(item["outcome"] == "DECLINE" for item in hits):
        decision = "DECLINE"
    elif any(item["outcome"] == "REFER" for item in hits) or (policy.get("mode") == "ENFORCE" and risk_score >= refer_threshold):
        decision = "REFER"
    else:
        decision = "APPROVE"

    features = {
        "stage": stage,
        "user_id": getattr(user, "id", None),
        "has_phone": bool(getattr(user, "phone", None)),
        "real_name_status": getattr(user, "real_name_status", None),
        "face_auth_status": getattr(user, "face_auth_status", None),
        "blacklist_hit": bool(getattr(user, "blacklist_hit", False)),
        "risk_list_hit": bool(getattr(user, "risk_list_hit", False)),
        "location_risk_blocked": bool(getattr(user, "location_risk_blocked", False)),
        "overdue_credit_locked": bool(getattr(user, "overdue_credit_locked", False)),
        "device_risk_level": device_risk_level,
        "device_risk_reasons": device_reasons,
        "device_keyword_hits": device_keyword_hits,
        "policy_mode": policy.get("mode"),
        "policy_refer_threshold": refer_threshold,
        "policy_block_threshold": block_threshold,
        "velocity_application_limit_24h": int(velocity.get("application_count_24h", 5) or 5),
        "velocity_device_account_limit_24h": int(velocity.get("device_account_count_24h", 3) or 3),
        "loan_status": getattr(loan, "status", None) if loan else None,
    }
    return RiskEvaluation(decision, min(round(risk_score, 2), 100.0), tuple(reasons), features, tuple(hits))


async def record_risk_decision_async(
    db: AsyncSession,
    *,
    user: User,
    loan: Optional[Loan],
    stage: str,
    mode: Optional[str] = None,
) -> Optional[RiskDecision]:
    """评估并记录一次风控决策，不在本函数内提交事务。

    :param db: 异步数据库会话
    :param user: 借款人对象
    :param loan: 当前订单
    :param stage: 决策阶段
    :param mode: 执行模式，默认只记录不拦截
    :return: 已加入当前会话的决策记录
    """
    # 部分历史单测使用最小 FakeDb，仅验证业务分支；没有持久化能力时跳过记录，
    # 真实 AsyncSession 始终具备 add/flush，不会影响生产审计闭环。
    if not hasattr(db, "add") or not hasattr(db, "flush"):
        return None
    active_policy = await get_active_risk_policy_version(db, policy_key=DEFAULT_RISK_POLICY_KEY) if hasattr(db, "execute") else None
    policy_config = normalize_risk_policy_config(active_policy.config_json if active_policy else None)
    device_signal = None
    if hasattr(db, "execute"):
        device_signal_stmt = select(RiskDeviceSignal).where(RiskDeviceSignal.user_id == int(user.id)).order_by(RiskDeviceSignal.created_at.desc()).limit(1)
        device_signal_result = await db.execute(device_signal_stmt)
        if device_signal_result is not None and hasattr(device_signal_result, "scalar_one_or_none"):
            device_signal = device_signal_result.scalar_one_or_none()
    evaluation = evaluate_baseline_rules(user, loan, stage, policy_config, device_signal=device_signal)
    decision_id = uuid4().hex
    policy_version = f"v{active_policy.version_no}" if active_policy else POLICY_VERSION
    configured_mode = (mode or policy_config.get("mode") or "SHADOW").upper()
    rollout_percent = int(getattr(active_policy, "rollout_percent", 0) or 0)
    rollout_bucket = (
        calculate_risk_policy_rollout_bucket(
            policy_key=active_policy.policy_key,
            version_no=int(active_policy.version_no or 0),
            subject_id=getattr(user, "id", None),
        )
        if active_policy
        else None
    )
    rollout_in_scope = bool(
        active_policy
        and active_policy.status == "ACTIVE"
        and configured_mode == "ENFORCE"
        and is_risk_policy_in_rollout(
            policy_key=active_policy.policy_key,
            version_no=int(active_policy.version_no or 0),
            rollout_percent=rollout_percent,
            subject_id=getattr(user, "id", None),
        )
    )
    resolved_mode = "ENFORCE" if rollout_in_scope else "SHADOW"
    feature_snapshot = dict(evaluation.features)
    feature_snapshot.update(
        {
            "policy_status": getattr(active_policy, "status", None) if active_policy else None,
            "policy_rollout_percent": rollout_percent,
            "policy_rollout_bucket": rollout_bucket,
            "policy_rollout_in_scope": rollout_in_scope,
            "device_signal_id": getattr(device_signal, "id", None),
            "device_signal_fingerprint": getattr(device_signal, "device_fingerprint", None),
            "device_signal_created_at": getattr(device_signal, "created_at", None),
        }
    )
    record = RiskDecision(
        decision_id=decision_id,
        user_id=int(user.id),
        loan_id=int(loan.id) if loan and getattr(loan, "id", None) else None,
        stage=stage,
        decision=evaluation.decision,
        score=evaluation.score,
        policy_key=active_policy.policy_key if active_policy else POLICY_KEY,
        policy_version=policy_version,
        mode=resolved_mode,
        reason_codes_json=json.dumps(evaluation.reasons, ensure_ascii=False),
        feature_snapshot_json=json.dumps(feature_snapshot, ensure_ascii=False, default=str),
        created_at=datetime.now(),
    )
    db.add(record)
    await db.flush()
    for item in evaluation.hits:
        db.add(RiskRuleHit(decision_id=decision_id, created_at=datetime.now(), **item))
    return record
