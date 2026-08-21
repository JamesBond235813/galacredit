import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_expansion import RiskDeviceSignal, RiskExternalCheck, RiskModelScore


@dataclass(frozen=True)
class RuleScore:
    """规则评分和额度建议。"""

    fraud_score: float
    credit_score: float
    decision: str
    recommended_limit: float
    reasons: tuple[str, ...]


def calculate_rule_scores(*, identity_verified: bool, face_verified: bool, blacklist_hit: bool,
                          overdue_days: int = 0, application_count_24h: int = 0,
                          device_account_count_24h: int = 0, wallet_match: bool = True) -> RuleScore:
    """计算可解释的欺诈分、信用分和首期额度建议。

    :param identity_verified: 是否实名通过
    :param face_verified: 是否人脸通过
    :param blacklist_hit: 是否命中黑名单
    :param overdue_days: 当前最大逾期天数
    :param application_count_24h: 24小时申请次数
    :param device_account_count_24h: 设备关联账户数
    :param wallet_match: 收款钱包是否与实名一致
    :return: 规则评分结果
    """
    fraud = 0.0
    credit = 50.0
    reasons: list[str] = []
    if blacklist_hit:
        fraud += 100; reasons.append("BLACKLIST_HIT")
    if not wallet_match:
        fraud += 35; reasons.append("WALLET_MISMATCH")
    if application_count_24h >= 5:
        fraud += 25; reasons.append("APPLICATION_VELOCITY_HIGH")
    if device_account_count_24h >= 3:
        fraud += 25; reasons.append("DEVICE_ACCOUNT_VELOCITY_HIGH")
    if identity_verified:
        credit += 20
    else:
        reasons.append("IDENTITY_NOT_VERIFIED")
    if face_verified:
        credit += 10
    else:
        reasons.append("FACE_NOT_VERIFIED")
    if overdue_days > 0:
        credit -= min(overdue_days * 3, 40); reasons.append("CURRENT_OVERDUE")
    decision = "BLOCK" if fraud >= 80 else "REFER" if fraud >= 35 or credit < 45 else "APPROVE"
    limit = 0.0 if decision == "BLOCK" else 500.0 if decision == "REFER" else 1000.0
    return RuleScore(round(fraud, 2), round(max(0, min(100, credit)), 2), decision, limit, tuple(reasons))


async def record_device_signal(db: AsyncSession, *, user_id: int, payload: dict[str, Any]) -> RiskDeviceSignal:
    """保存设备/IP/速度特征，并返回记录。

    :param db: 异步数据库会话
    :param user_id: 用户ID
    :param payload: 已脱敏的设备特征
    :return: 特征记录
    """
    record = RiskDeviceSignal(user_id=user_id, device_fingerprint=payload.get("device_fingerprint"),
                              ip_address=payload.get("ip_address"), asn=payload.get("asn"),
                              is_proxy=int(bool(payload.get("is_proxy"))), is_emulator=int(bool(payload.get("is_emulator"))),
                              application_count_24h=int(payload.get("application_count_24h") or 0),
                              account_count_24h=int(payload.get("account_count_24h") or 0),
                              payload_json=json.dumps(payload, ensure_ascii=False))
    db.add(record)
    await db.flush()
    return record


async def count_device_velocity(db: AsyncSession, *, device_fingerprint: str, since: Optional[datetime] = None) -> int:
    """统计设备近期关联账户数，用于速度风控。

    :param db: 异步数据库会话
    :param device_fingerprint: 设备指纹
    :param since: 起始时间，默认最近24小时
    :return: 去重用户数量
    """
    since = since or datetime.now() - timedelta(hours=24)
    value = await db.scalar(select(func.count(func.distinct(RiskDeviceSignal.user_id))).where(
        RiskDeviceSignal.device_fingerprint == device_fingerprint, RiskDeviceSignal.created_at >= since))
    return int(value or 0)


async def record_external_check(db: AsyncSession, *, user_id: int, provider: str, check_type: str,
                                status: str = "SKIPPED", score: Optional[float] = None,
                                reason: Optional[str] = None, response: Optional[dict[str, Any]] = None) -> RiskExternalCheck:
    """记录外部数据查询，供应商不可用时保留安全降级轨迹。

    :param db: 异步数据库会话
    :param user_id: 用户ID
    :param provider: 供应商标识
    :param check_type: 查询类型
    :param status: 查询状态
    :param score: 外部评分
    :param reason: 结果说明
    :param response: 脱敏响应
    :return: 查询记录
    """
    record = RiskExternalCheck(user_id=user_id, provider=provider, check_type=check_type, status=status,
                               score=score, reason=reason, response_json=json.dumps(response or {}, ensure_ascii=False))
    db.add(record)
    await db.flush()
    return record


async def record_model_score(db: AsyncSession, *, decision_id: str, model_key: str, model_version: str,
                             score: float, explanation: dict[str, Any], mode: str = "SHADOW") -> RiskModelScore:
    """记录模型评分，默认 shadow 以支持 champion/challenger 对比。

    :param db: 异步数据库会话
    :param decision_id: 决策流水号
    :param model_key: 模型标识
    :param model_version: 模型版本
    :param score: 模型评分
    :param explanation: 解释因子
    :param mode: 执行模式
    :return: 模型评分记录
    """
    record = RiskModelScore(decision_id=decision_id, model_key=model_key, model_version=model_version,
                            score=score, mode=mode, explanation_json=json.dumps(explanation, ensure_ascii=False))
    db.add(record)
    await db.flush()
    return record
