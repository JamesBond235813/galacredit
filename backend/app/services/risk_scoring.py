import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence

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


DEVICE_SMS_KEYWORDS = {
    "loan": ("loan", "borrow", "credit", "cash", "advance", "repayment"),
    "overdue": ("overdue", "default", "collections", "past due", "late fee"),
    "payment": ("payment", "transfer", "mobile money", "momo", "withdraw", "disburse"),
    "gambling": ("bet", "casino", "stake", "jackpot", "sportsbook"),
    "fraud": ("root", "emulator", "clone", "cloned", "mock location", "developer mode", "vpn"),
}

DEVICE_APP_KEYWORDS = {
    "loan": ("loan", "cash", "credit"),
    "overdue": ("debt", "collection", "collections", "repay"),
    "payment": ("momo", "wallet", "bank", "transfer"),
    "gambling": ("bet", "casino", "sportsbook"),
    "fraud": ("emulator", "clone", "cloner", "vpn", "hook"),
}

DEVICE_ENVIRONMENT_KEYWORDS = {
    "root": ("root", "su", "magisk"),
    "emulator": ("emulator", "genymotion", "sdk", "bluestacks"),
    "cloned": ("clone", "dual space", "parallel space"),
    "developer_mode": ("developer", "usb debugging", "debugging"),
    "vpn": ("vpn", "proxy", "tunnel"),
}


def _normalize_text(value: Any) -> str:
    """将任意输入规范化为便于匹配的文本。

    :param value: 原始值
    :return: 统一小写文本
    """
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", " ").split()).strip().lower()


def _collect_keyword_hits(text: str, catalog: dict[str, Sequence[str]]) -> list[str]:
    """从文本中提取关键词命中。

    :param text: 待匹配文本
    :param catalog: 关键词目录
    :return: 命中关键词分类
    """
    if not text:
        return []
    hits: list[str] = []
    for label, keywords in catalog.items():
        if any(keyword in text for keyword in keywords):
            hits.append(label)
    return hits


def _merge_unique(values: Sequence[str]) -> list[str]:
    """按原始顺序去重。

    :param values: 待去重值
    :return: 去重后的列表
    """
    merged: list[str] = []
    for item in values:
        if item and item not in merged:
            merged.append(item)
    return merged


def build_device_fingerprint(*, payload: dict[str, Any]) -> str:
    """生成不可逆的设备摘要指纹。

    :param payload: 设备采集载荷
    :return: 设备指纹哈希
    """
    # 仅使用稳定的设备特征生成摘要，避免短信/应用列表等动态内容导致指纹漂移。
    stable = {
        "device_fingerprint": payload.get("device_fingerprint"),
        "platform": payload.get("platform"),
        "device_profile": payload.get("device_profile") or {},
    }
    source = json.dumps(stable, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def summarize_device_collection(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """将原始采集内容整理为适合存储和审计的摘要。

    :param payload: 原始设备采集载荷
    :return: 结构化摘要
    """
    sms_rows = []
    for item in payload.get("sms_messages") or []:
        text = _normalize_text(" ".join(str(part or "") for part in [item.get("sender"), item.get("title"), item.get("body")]))
        sms_rows.append(
            {
                "sender": str(item.get("sender") or "")[:80],
                "title": str(item.get("title") or "")[:120],
                "body": str(item.get("body") or "")[:500],
                "keywords": _merge_unique(_collect_keyword_hits(text, DEVICE_SMS_KEYWORDS)),
            }
        )

    app_rows = []
    for item in payload.get("installed_apps") or []:
        text = _normalize_text(" ".join(str(part or "") for part in [item.get("name"), item.get("package")]))
        app_rows.append(
            {
                "name": str(item.get("name") or "")[:120],
                "package": str(item.get("package") or "")[:120],
                "keywords": _merge_unique(_collect_keyword_hits(text, DEVICE_APP_KEYWORDS)),
            }
        )

    device_profile = dict(payload.get("device_profile") or {})
    device_text = _normalize_text(
        " ".join(
            str(part or "")
            for part in [
                device_profile.get("model"),
                device_profile.get("manufacturer"),
                device_profile.get("os"),
                device_profile.get("os_version"),
                device_profile.get("browser"),
                device_profile.get("browser_version"),
                payload.get("platform"),
                payload.get("browser_name"),
                payload.get("browser_version"),
                payload.get("timezone"),
                payload.get("language"),
            ]
        )
    )
    environment_hits = _merge_unique(_collect_keyword_hits(device_text, DEVICE_ENVIRONMENT_KEYWORDS))
    device_summary = {
        "source": payload.get("source") or "H5",
        "native_bridge": payload.get("native_bridge"),
        "device_profile": device_profile,
        "screen_width": payload.get("screen_width"),
        "screen_height": payload.get("screen_height"),
        "timezone": payload.get("timezone"),
        "language": payload.get("language"),
        "browser_name": payload.get("browser_name"),
        "browser_version": payload.get("browser_version"),
        "platform": payload.get("platform"),
    }
    sms_keywords = _merge_unique(sum((item["keywords"] for item in sms_rows), []))
    app_keywords = _merge_unique(sum((item["keywords"] for item in app_rows), []))
    risk_flags = _merge_unique(list(payload.get("risk_flags") or []) + environment_hits)
    return {
        "sms_summary": sms_rows,
        "app_summary": app_rows,
        "device_summary": device_summary,
        "sms_keywords": sms_keywords,
        "app_keywords": app_keywords,
        "environment_hits": environment_hits,
        "risk_flags": risk_flags,
        "device_fingerprint": payload.get("device_fingerprint") or build_device_fingerprint(payload=payload),
    }


def evaluate_device_risk_signals(*, summary: dict[str, Any], shared_device_count: int = 0) -> tuple[str, list[str], dict[str, list[str]], list[str]]:
    """根据设备摘要生成风控标签和命中项。

    :param summary: 结构化设备摘要
    :param shared_device_count: 同设备近端关联用户数
    :return: 风险等级、原因码、关键词命中、风险标记
    """
    sms_keywords = list(summary.get("sms_keywords") or [])
    app_keywords = list(summary.get("app_keywords") or [])
    environment_hits = list(summary.get("environment_hits") or [])
    risk_flags = list(summary.get("risk_flags") or [])
    reasons: list[str] = []
    keyword_hits = {
        "sms": sms_keywords,
        "apps": app_keywords,
        "device": environment_hits,
    }

    if "fraud" in environment_hits or {"root", "emulator"} & set(environment_hits):
        reasons.append("DEVICE_ENV_HIGH_RISK")
    if "loan" in sms_keywords and "overdue" in sms_keywords:
        reasons.append("SMS_LOAN_OVERDUE")
    if "gambling" in sms_keywords or "gambling" in app_keywords:
        reasons.append("GAMBLING_SIGNAL")
    if "loan" in app_keywords and "overdue" in app_keywords:
        reasons.append("APP_DEBT_PRESSURE")
    if shared_device_count >= 3:
        reasons.append("DEVICE_SHARED_MULTI_USER")

    if reasons or risk_flags:
        risk_level = "HIGH" if any(item in {"DEVICE_ENV_HIGH_RISK", "SMS_LOAN_OVERDUE", "GAMBLING_SIGNAL"} for item in reasons) else "MEDIUM"
    elif sms_keywords or app_keywords or environment_hits:
        risk_level = "LOW"
    else:
        risk_level = "INFO"
    if shared_device_count >= 5:
        risk_level = "HIGH"
    return risk_level, _merge_unique(reasons), keyword_hits, _merge_unique(risk_flags)


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
    summary = summarize_device_collection(payload=payload)
    shared_device_count = int(payload.get("account_count_24h") or 0)
    risk_level, reasons, keyword_hits, risk_flags = evaluate_device_risk_signals(
        summary=summary,
        shared_device_count=shared_device_count,
    )
    record = RiskDeviceSignal(
        user_id=user_id,
        consent_granted=int(bool(payload.get("consent_granted"))),
        # 服务端统一生成不可逆指纹，不直接保存客户端传入的 Android ID。
        device_fingerprint=build_device_fingerprint(payload=payload),
        ip_address=payload.get("ip_address"),
        asn=payload.get("asn"),
        is_proxy=int(bool(payload.get("is_proxy"))),
        is_emulator=int(bool(payload.get("is_emulator"))),
        application_count_24h=int(payload.get("application_count_24h") or 0),
        account_count_24h=shared_device_count,
        collected_channel=str(payload.get("source") or "H5")[:30],
        risk_level=risk_level,
        keyword_hits_json=json.dumps(keyword_hits, ensure_ascii=False),
        sms_summary_json=json.dumps(summary.get("sms_summary") or [], ensure_ascii=False),
        app_summary_json=json.dumps(summary.get("app_summary") or [], ensure_ascii=False),
        device_summary_json=json.dumps(summary.get("device_summary") or {}, ensure_ascii=False),
        risk_flags_json=json.dumps({"reasons": reasons, "risk_flags": risk_flags}, ensure_ascii=False),
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
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
