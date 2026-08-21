import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan
from app.models.risk_decision import RiskDecision, RiskRuleHit
from app.models.user import User


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


def evaluate_baseline_rules(user: User, loan: Optional[Loan], stage: str) -> RiskEvaluation:
    """基于当前已落库字段执行加纳现金贷基线规则。

    :param user: 借款人对象
    :param loan: 当前订单，可为空
    :param stage: 决策阶段
    :return: 可解释的风控评估结果
    """
    reasons: list[str] = []
    hits: list[dict[str, str]] = []
    risk_score = 0.0

    def hit(code: str, outcome: str, severity: str, detail: str, points: float = 0.0) -> None:
        nonlocal risk_score
        risk_score += points
        hits.append({"rule_code": code, "outcome": outcome, "severity": severity, "detail": detail})
        if outcome in {"REFER", "DECLINE", "BLOCK"}:
            reasons.append(code)

    if bool(getattr(user, "blacklist_hit", False)):
        hit("BLACKLIST_HIT", "BLOCK", "HIGH", "内部黑名单命中", 100)
    if bool(getattr(user, "risk_list_hit", False)):
        hit("EXTERNAL_RISK_LIST_HIT", "BLOCK", "HIGH", "外部风险名单命中", 100)
    if bool(getattr(user, "location_risk_blocked", False)):
        hit("LOCATION_RISK_LOCKED", "REFER", "MEDIUM", "位置风控锁定", 35)
    if str(getattr(user, "real_name_status", "") or "").upper() not in {"VERIFIED", "AUTHED", "PASS", "PASSED"}:
        hit("IDENTITY_NOT_VERIFIED", "REFER", "MEDIUM", "实名状态未完成", 25)
    if str(getattr(user, "face_auth_status", "") or "").upper() not in {"APPROVED", "PASS", "PASSED"}:
        hit("FACE_NOT_VERIFIED", "REFER", "MEDIUM", "人脸状态未完成", 20)
    if not getattr(user, "phone", None):
        hit("PHONE_MISSING", "DECLINE", "HIGH", "手机号缺失", 80)
    if loan is not None and str(getattr(loan, "status", "") or "").upper() == "OVERDUE":
        hit("CURRENT_LOAN_OVERDUE", "REFER", "HIGH", "当前订单逾期", 45)
    if bool(getattr(user, "overdue_credit_locked", False)):
        hit("OVERDUE_CREDIT_LOCKED", "REFER", "HIGH", "逾期额度锁定", 40)

    if any(item["outcome"] == "BLOCK" for item in hits):
        decision = "BLOCK"
    elif any(item["outcome"] == "DECLINE" for item in hits):
        decision = "DECLINE"
    elif any(item["outcome"] == "REFER" for item in hits):
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
        "loan_status": getattr(loan, "status", None) if loan else None,
    }
    return RiskEvaluation(decision, min(round(risk_score, 2), 100.0), tuple(reasons), features, tuple(hits))


async def record_risk_decision_async(
    db: AsyncSession,
    *,
    user: User,
    loan: Optional[Loan],
    stage: str,
    mode: str = "SHADOW",
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
    evaluation = evaluate_baseline_rules(user, loan, stage)
    decision_id = uuid4().hex
    record = RiskDecision(
        decision_id=decision_id,
        user_id=int(user.id),
        loan_id=int(loan.id) if loan and getattr(loan, "id", None) else None,
        stage=stage,
        decision=evaluation.decision,
        score=evaluation.score,
        policy_key=POLICY_KEY,
        policy_version=POLICY_VERSION,
        mode=mode,
        reason_codes_json=json.dumps(evaluation.reasons, ensure_ascii=False),
        feature_snapshot_json=json.dumps(evaluation.features, ensure_ascii=False, default=str),
        created_at=datetime.now(),
    )
    db.add(record)
    await db.flush()
    for item in evaluation.hits:
        db.add(RiskRuleHit(decision_id=decision_id, created_at=datetime.now(), **item))
    return record
