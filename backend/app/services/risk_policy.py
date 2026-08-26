import json
import hashlib
from copy import deepcopy
from datetime import datetime
from typing import Any, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException
from app.models.risk_decision import RiskPolicyVersion


DEFAULT_RISK_POLICY_KEY = "GHANA_CASH_LOAN_BASELINE"
VALID_RISK_POLICY_STATUSES = {"DRAFT", "SHADOW", "ACTIVE", "DISABLED"}


def build_default_risk_policy_config() -> dict[str, Any]:
    """构造默认风控策略配置。

    :return: 默认策略配置字典
    """
    return {
        "policy_name": "Ghana cash-loan baseline rules",
        "description": "Default baseline policy for Ghana cash-loan risk management.",
        "mode": "SHADOW",
        "decision_thresholds": {
            "refer_score": 35,
            "block_score": 80,
        },
        "rule_points": {
            "BLACKLIST_HIT": 100,
            "EXTERNAL_RISK_LIST_HIT": 100,
            "LOCATION_RISK_LOCKED": 35,
            "IDENTITY_NOT_VERIFIED": 25,
            "FACE_NOT_VERIFIED": 20,
        "PHONE_MISSING": 80,
        "CURRENT_LOAN_OVERDUE": 45,
        "OVERDUE_CREDIT_LOCKED": 40,
        "DEVICE_ENV_HIGH_RISK": 70,
        "SMS_LOAN_OVERDUE": 45,
        "GAMBLING_SIGNAL": 35,
        "APP_DEBT_PRESSURE": 30,
        "DEVICE_SHARED_MULTI_USER": 40,
    },
        "rule_enables": {
            "BLACKLIST_HIT": True,
            "EXTERNAL_RISK_LIST_HIT": True,
            "LOCATION_RISK_LOCKED": True,
            "IDENTITY_NOT_VERIFIED": True,
            "FACE_NOT_VERIFIED": True,
        "PHONE_MISSING": True,
        "CURRENT_LOAN_OVERDUE": True,
        "OVERDUE_CREDIT_LOCKED": True,
        "DEVICE_ENV_HIGH_RISK": True,
        "SMS_LOAN_OVERDUE": True,
        "GAMBLING_SIGNAL": True,
        "APP_DEBT_PRESSURE": True,
        "DEVICE_SHARED_MULTI_USER": True,
    },
        "velocity": {
            "application_count_24h": 5,
            "device_account_count_24h": 3,
        },
    }


def normalize_risk_policy_config(raw_config: Any) -> dict[str, Any]:
    """标准化策略配置，确保缺省字段和类型可用。

    :param raw_config: 原始配置对象
    :return: 标准化后的配置字典
    """
    if raw_config in (None, ""):
        return build_default_risk_policy_config()
    if isinstance(raw_config, str):
        try:
            decoded = json.loads(raw_config)
        except json.JSONDecodeError as exc:
            raise BizException("Invalid risk policy config json", code=400) from exc
    elif isinstance(raw_config, dict):
        decoded = deepcopy(raw_config)
    else:
        try:
            decoded = dict(raw_config)
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise BizException("Invalid risk policy config payload", code=400) from exc

    base = build_default_risk_policy_config()

    def _merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
        for key, value in src.items():
            if isinstance(value, dict) and isinstance(dst.get(key), dict):
                dst[key] = _merge(dict(dst[key]), value)
            else:
                dst[key] = value
        return dst

    merged = _merge(base, decoded)
    merged["mode"] = str(merged.get("mode") or "SHADOW").strip().upper()
    thresholds = merged.get("decision_thresholds") or {}
    merged["decision_thresholds"] = {
        "refer_score": int(thresholds.get("refer_score", 35) or 35),
        "block_score": int(thresholds.get("block_score", 80) or 80),
    }
    rule_points = merged.get("rule_points") or {}
    merged["rule_points"] = {key: float(value) for key, value in rule_points.items()}
    rule_enables = merged.get("rule_enables") or {}
    merged["rule_enables"] = {key: bool(value) for key, value in rule_enables.items()}
    velocity = merged.get("velocity") or {}
    merged["velocity"] = {
        "application_count_24h": int(velocity.get("application_count_24h", 5) or 5),
        "device_account_count_24h": int(velocity.get("device_account_count_24h", 3) or 3),
    }
    return merged


def serialize_risk_policy_version(row: RiskPolicyVersion) -> dict[str, Any]:
    """序列化策略版本记录。

    :param row: 风控策略版本对象
    :return: 可直接返回前端的字典
    """
    config = normalize_risk_policy_config(row.config_json)
    return {
        "id": row.id,
        "policy_key": row.policy_key,
        "version_no": row.version_no,
        "status": row.status,
        "rollout_percent": int(row.rollout_percent or 0),
        "config_json": config,
        "config_summary": {
            "policy_name": config.get("policy_name"),
            "description": config.get("description"),
            "mode": config.get("mode"),
            "decision_thresholds": config.get("decision_thresholds"),
            "rule_points": config.get("rule_points"),
        },
        "created_by": row.created_by,
        "created_at": row.created_at,
        "is_active": row.status == "ACTIVE",
    }


def calculate_risk_policy_rollout_bucket(*, policy_key: str, version_no: int, subject_id: Any) -> int:
    """计算策略灰度命中桶值。

    :param policy_key: 策略标识
    :param version_no: 策略版本号
    :param subject_id: 参与灰度分流的主体标识
    :return: 0 到 99 之间的稳定桶值
    """
    raw = f"{policy_key}:{version_no}:{subject_id}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return int(digest[:8], 16) % 100


def is_risk_policy_in_rollout(*, policy_key: str, version_no: int, rollout_percent: int, subject_id: Any) -> bool:
    """判断主体是否命中策略灰度范围。

    :param policy_key: 策略标识
    :param version_no: 策略版本号
    :param rollout_percent: 灰度比例
    :param subject_id: 参与灰度分流的主体标识
    :return: 是否命中灰度范围
    """
    rollout_percent = max(0, min(100, int(rollout_percent or 0)))
    if rollout_percent <= 0:
        return False
    if rollout_percent >= 100:
        return True
    return calculate_risk_policy_rollout_bucket(
        policy_key=policy_key,
        version_no=version_no,
        subject_id=subject_id,
    ) < rollout_percent


async def ensure_default_risk_policy_version(db: AsyncSession) -> None:
    """确保默认风控策略版本存在。

    :param db: 异步数据库会话
    :return: 无返回值
    """
    try:
        exists = await db.scalar(select(RiskPolicyVersion.id).where(RiskPolicyVersion.policy_key == DEFAULT_RISK_POLICY_KEY).limit(1))
    except ProgrammingError as exc:
        # 启动自检只负责兜底种子，不应因为远端表尚未完全可用而把整个后端拉成 502。
        if getattr(getattr(exc, "orig", None), "args", [None])[0] == 1146:
            return
        raise
    if exists:
        return
    try:
        db.add(
            RiskPolicyVersion(
                policy_key=DEFAULT_RISK_POLICY_KEY,
                version_no=1,
                status="SHADOW",
                config_json=json.dumps(build_default_risk_policy_config(), ensure_ascii=False),
                rollout_percent=0,
                created_by="SYSTEM",
                created_at=datetime.now(),
            )
        )
        await db.commit()
    except ProgrammingError as exc:
        if getattr(getattr(exc, "orig", None), "args", [None])[0] == 1146:
            return
        raise


async def list_risk_policy_versions(
    db: AsyncSession,
    *,
    policy_key: Optional[str] = None,
) -> list[RiskPolicyVersion]:
    """查询策略版本列表。

    :param db: 异步数据库会话
    :param policy_key: 策略标识
    :return: 策略版本列表
    """
    stmt = select(RiskPolicyVersion).order_by(RiskPolicyVersion.policy_key.asc(), RiskPolicyVersion.version_no.desc())
    if policy_key:
        stmt = stmt.where(RiskPolicyVersion.policy_key == policy_key)
    return list((await db.execute(stmt)).scalars().all())


async def get_active_risk_policy_version(
    db: AsyncSession,
    *,
    policy_key: str = DEFAULT_RISK_POLICY_KEY,
) -> Optional[RiskPolicyVersion]:
    """获取当前启用的策略版本。

    :param db: 异步数据库会话
    :param policy_key: 策略标识
    :return: 当前启用的策略版本
    """
    stmt = (
        select(RiskPolicyVersion)
        .where(RiskPolicyVersion.policy_key == policy_key)
        .order_by(RiskPolicyVersion.version_no.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    for row in rows:
        if row.status == "ACTIVE":
            return row
    return rows[0] if rows else None


async def create_risk_policy_version(
    db: AsyncSession,
    *,
    policy_key: str,
    config_json: Any,
    status: str,
    rollout_percent: int,
    created_by: Optional[str] = None,
) -> RiskPolicyVersion:
    """创建新的策略版本。

    :param db: 异步数据库会话
    :param policy_key: 策略标识
    :param config_json: 策略配置
    :param status: 初始状态
    :param rollout_percent: 灰度比例
    :param created_by: 创建人
    :return: 新增的策略版本
    """
    policy_key = str(policy_key or DEFAULT_RISK_POLICY_KEY).strip()
    status = str(status or "DRAFT").strip().upper()
    if status not in VALID_RISK_POLICY_STATUSES:
        raise BizException("Invalid policy status", code=400)
    rollout_percent = max(0, min(100, int(rollout_percent or 0)))
    normalized_config = normalize_risk_policy_config(config_json)
    max_version = await db.scalar(
        select(func.coalesce(func.max(RiskPolicyVersion.version_no), 0)).where(RiskPolicyVersion.policy_key == policy_key)
    )
    row = RiskPolicyVersion(
        policy_key=policy_key,
        version_no=int(max_version or 0) + 1,
        status=status,
        config_json=json.dumps(normalized_config, ensure_ascii=False),
        rollout_percent=rollout_percent,
        created_by=created_by,
        created_at=datetime.now(),
    )
    db.add(row)
    await db.flush()
    return row


async def update_risk_policy_version(
    db: AsyncSession,
    *,
    version_id: int,
    config_json: Any,
    status: str,
    rollout_percent: int,
) -> RiskPolicyVersion:
    """更新策略版本配置。

    :param db: 异步数据库会话
    :param version_id: 版本ID
    :param config_json: 策略配置
    :param status: 状态
    :param rollout_percent: 灰度比例
    :return: 更新后的策略版本
    """
    row = await db.get(RiskPolicyVersion, version_id)
    if row is None:
        raise BizException("Risk policy version not found", code=404)
    status = str(status or row.status).strip().upper()
    if status not in VALID_RISK_POLICY_STATUSES:
        raise BizException("Invalid policy status", code=400)
    row.config_json = json.dumps(normalize_risk_policy_config(config_json), ensure_ascii=False)
    row.status = status
    row.rollout_percent = max(0, min(100, int(rollout_percent or 0)))
    await db.flush()
    return row


async def copy_risk_policy_version(
    db: AsyncSession,
    *,
    version_id: int,
    created_by: Optional[str] = None,
) -> RiskPolicyVersion:
    """复制一个策略版本并生成新版本号。

    :param db: 异步数据库会话
    :param version_id: 被复制的版本ID
    :param created_by: 创建人
    :return: 新复制出来的策略版本
    """
    source = await db.get(RiskPolicyVersion, version_id)
    if source is None:
        raise BizException("Risk policy version not found", code=404)
    max_version = await db.scalar(
        select(func.coalesce(func.max(RiskPolicyVersion.version_no), 0)).where(RiskPolicyVersion.policy_key == source.policy_key)
    )
    copied = RiskPolicyVersion(
        policy_key=source.policy_key,
        version_no=int(max_version or 0) + 1,
        status="DRAFT",
        config_json=source.config_json,
        rollout_percent=int(source.rollout_percent or 0),
        created_by=created_by,
        created_at=datetime.now(),
    )
    db.add(copied)
    await db.flush()
    return copied


async def activate_risk_policy_version(db: AsyncSession, *, version_id: int) -> RiskPolicyVersion:
    """激活指定策略版本，并将同策略下其他 ACTIVE 版本切回 SHADOW。

    :param db: 异步数据库会话
    :param version_id: 版本ID
    :return: 激活后的版本
    """
    row = await db.get(RiskPolicyVersion, version_id)
    if row is None:
        raise BizException("Risk policy version not found", code=404)
    if row.status == "DISABLED":
        raise BizException("Disabled policy version cannot be activated", code=400)
    rows = (await db.execute(select(RiskPolicyVersion).where(RiskPolicyVersion.policy_key == row.policy_key))).scalars().all()
    for item in rows:
        if item.id == row.id:
            item.status = "ACTIVE"
        elif item.status == "ACTIVE":
            item.status = "SHADOW"
    await db.flush()
    return row


async def disable_risk_policy_version(db: AsyncSession, *, version_id: int) -> RiskPolicyVersion:
    """停用指定策略版本。

    :param db: 异步数据库会话
    :param version_id: 版本ID
    :return: 停用后的版本
    """
    row = await db.get(RiskPolicyVersion, version_id)
    if row is None:
        raise BizException("Risk policy version not found", code=404)
    row.status = "DISABLED"
    await db.flush()
    return row
