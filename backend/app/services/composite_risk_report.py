import json
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models.blacklist import BlacklistEntry
from app.models.loan import Loan
from app.models.phone_binding import UserPhoneBinding
from app.models.risk_composite_report import RiskCompositeReport
from app.models.risk_report import RiskControlReport
from app.models.user import User
from app.models.user_event import UserEvent
from app.services.loan_amounts import calculate_remaining_repayment_amount, serialize_loan_snapshot
from app.services.risk_report import RISK_SOURCE_PROBE_C, get_or_create_probe_c_report_async, get_or_create_risk_report_async

RISK_LOCATION_KEYWORDS = tuple(
    dict.fromkeys(
        [
            "潍坊",
            "瓦房店",
            "聊城",
            "无锡",
            "宜兴",
            "日照",
            "烟台",
            "新疆",
            "长沙",
            "鹿泉区汇源街",
            "大连",
            "张家口",
            "葫芦岛",
            "内蒙古",
        ]
    )
)
RISK_LOCATION_OVERSEAS_KEYWORD = "中国大陆境外"
MAINLAND_COUNTRY_NAMES = {"中国", "中国大陆", "中华人民共和国"}


def serialize_composite_risk_report(report: RiskCompositeReport) -> Dict[str, Any]:
    """序列化综合风险报告。

    :param report: 综合风险报告对象
    :return: 综合风险报告响应
    """
    probe_report_id = getattr(report, "probe_c_report_id", None) or getattr(report, "probe_a_report_id", None)
    return {
        "id": report.id,
        "user_id": report.user_id,
        "panorama_report_id": report.panorama_report_id,
        "probe_a_report_id": probe_report_id,
        "probe_c_report_id": probe_report_id,
        "name": report.name,
        "id_card": report.id_card,
        "phone": report.phone,
        "report_json": _normalize_xiaohebao_report_json(report.report_json),
        "query_time": report.query_time,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


async def get_cached_composite_report_async(
    db: AsyncSession,
    *,
    name: str,
    id_card: str,
    require_probe_c: bool = False,
) -> Optional[RiskCompositeReport]:
    """获取14天内的综合风险报告缓存。

    :param db: 异步数据库会话
    :param name: 姓名
    :param id_card: 身份证号
    :param require_probe_c: 是否仅允许复用探针C缓存
    :return: 综合风险报告
    """
    cache_days = min(int(getattr(settings, "RISK_REPORT_CACHE_DAYS", 14) or 14), 14)
    cache_start = datetime.now() - timedelta(days=cache_days)
    stmt = (
        select(RiskCompositeReport)
        .where(
            RiskCompositeReport.name == name,
            RiskCompositeReport.id_card == id_card,
            RiskCompositeReport.query_time >= cache_start,
        )
        .order_by(RiskCompositeReport.query_time.desc())
    )
    reports = (await db.execute(stmt.limit(10))).scalars().all()
    if not require_probe_c:
        return reports[0] if reports else None
    for report in reports:
        if _is_probe_c_composite_payload(report.report_json):
            return report
    return None


async def get_or_create_composite_risk_report_async(
    db: AsyncSession,
    *,
    user: User,
) -> RiskCompositeReport:
    """获取或创建综合风险报告。

    :param db: 异步数据库会话
    :param user: 用户对象
    :return: 综合风险报告
    """
    latest_status = await _get_latest_loan_status_async(db, user_id=user.id)
    cached_report = await get_cached_composite_report_async(
        db,
        name=user.name,
        id_card=user.id_card_num,
        require_probe_c=latest_status == "REVIEWING",
    )
    if cached_report:
        return cached_report

    panorama_report = await get_or_create_risk_report_async(
        db,
        name=user.name,
        id_card=user.id_card_num,
        phone=user.phone,
        user_id=user.id,
    )
    probe_c_report = await get_or_create_probe_c_report_async(
        db,
        name=user.name,
        id_card=user.id_card_num,
        phone=user.phone,
        user_id=user.id,
    )
    payload = await build_composite_risk_payload_async(
        db,
        user=user,
        panorama_report=panorama_report,
        probe_c_report=probe_c_report,
    )
    now = datetime.now()
    report = RiskCompositeReport(
        user_id=user.id,
        panorama_report_id=panorama_report.id,
        probe_a_report_id=probe_c_report.id,
        name=user.name,
        id_card=user.id_card_num,
        phone=user.phone,
        report_json=json.dumps(payload, ensure_ascii=False, default=_json_default),
        query_time=now,
        created_at=now,
        updated_at=now,
    )
    db.add(report)
    await db.flush()
    return report


async def get_or_create_standalone_composite_risk_report_async(
    db: AsyncSession,
    *,
    name: str,
    id_card: str,
    phone: str,
    user_id: Optional[int] = None,
) -> RiskCompositeReport:
    """获取或创建不依赖订单审批状态的单查风险报告。

    :param db: 异步数据库会话
    :param name: 姓名
    :param id_card: 身份证号
    :param phone: 手机号
    :param user_id: 匹配到的用户ID
    :return: 综合风险报告
    """
    cached_report = await get_cached_composite_report_async(db, name=name, id_card=id_card, require_probe_c=True)
    if cached_report:
        return cached_report

    panorama_report = await get_or_create_risk_report_async(
        db,
        name=name,
        id_card=id_card,
        phone=phone,
        user_id=user_id,
    )
    probe_c_report = await get_or_create_probe_c_report_async(
        db,
        name=name,
        id_card=id_card,
        phone=phone,
        user_id=user_id,
    )
    user = _build_standalone_user(name=name, id_card=id_card, phone=phone, user_id=user_id)
    payload = await build_composite_risk_payload_async(
        db,
        user=user,
        panorama_report=panorama_report,
        probe_c_report=probe_c_report,
    )
    now = datetime.now()
    report = RiskCompositeReport(
        user_id=user_id,
        panorama_report_id=panorama_report.id,
        probe_a_report_id=probe_c_report.id,
        name=name,
        id_card=id_card,
        phone=phone,
        report_json=json.dumps(payload, ensure_ascii=False, default=_json_default),
        query_time=now,
        created_at=now,
        updated_at=now,
    )
    db.add(report)
    await db.flush()
    return report


def _build_standalone_user(*, name: str, id_card: str, phone: str, user_id: Optional[int]) -> SimpleNamespace:
    """构造单查报告使用的轻量用户对象。

    :param name: 姓名
    :param id_card: 身份证号
    :param phone: 手机号
    :param user_id: 匹配到的用户ID
    :return: 轻量用户对象
    """
    now = datetime.now()
    return SimpleNamespace(
        id=user_id,
        name=name,
        phone=phone,
        id_card_num=id_card,
        id_address=None,
        created_at=now,
        real_name_status="STANDALONE",
        face_auth_status="UNKNOWN",
        ocr_submitted_at=None,
        application_submitted_at=None,
        last_login_at=None,
        blacklist_hit=False,
        blacklist_reason=None,
        blacklist_checked_at=None,
        risk_list_hit=False,
        risk_list_source=None,
        risk_list_reason=None,
        risk_list_checked_at=None,
        location_province=None,
        location_city=None,
        location_district=None,
        location_street=None,
        location_address=None,
        location_risk_blocked=False,
        location_risk_reason=None,
        location_risk_at=None,
        available_credit_limit=0,
        overdue_credit_locked=False,
    )


async def _get_latest_loan_status_async(db: AsyncSession, *, user_id: int) -> Optional[str]:
    """获取用户最近订单状态。

    :param db: 异步数据库会话
    :param user_id: 用户ID
    :return: 最近订单状态
    """
    stmt = select(Loan.status).where(Loan.user_id == user_id).order_by(Loan.id.desc()).limit(1)
    return (await db.execute(stmt)).scalars().first()


async def build_composite_risk_payload_async(
    db: AsyncSession,
    *,
    user: User,
    panorama_report: RiskControlReport,
    probe_c_report: RiskControlReport,
) -> Dict[str, Any]:
    """构建综合风险报告快照。

    :param db: 异步数据库会话
    :param user: 用户对象
    :param panorama_report: 全景雷达报告
    :param probe_c_report: 探针C报告
    :return: 综合风险报告JSON
    """
    latest_loan = (
        await db.execute(
            select(Loan)
            .options(joinedload(Loan.owner), joinedload(Loan.installments))
            .where(Loan.user_id == user.id)
            .order_by(Loan.id.desc())
            .limit(1)
        )
    ).unique().scalars().first()
    active_blacklist = (
        await db.execute(
            select(BlacklistEntry)
            .where(
                BlacklistEntry.removed_at.is_(None),
                (BlacklistEntry.phone == user.phone) | (BlacklistEntry.id_card_num == user.id_card_num),
            )
            .order_by(BlacklistEntry.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    phone_bindings = (
        await db.execute(
            select(UserPhoneBinding)
            .where(UserPhoneBinding.phone == user.phone)
            .order_by(UserPhoneBinding.created_at.desc())
            .limit(10)
        )
    ).scalars().all()
    recent_events = (
        await db.execute(
            select(UserEvent)
            .where(UserEvent.user_id == user.id)
            .order_by(UserEvent.created_at.desc())
            .limit(30)
        )
    ).scalars().all()
    location_risk = _resolve_user_location_risk(user, recent_events)
    panorama_payload = _strip_panorama_credit_detail(_parse_report_json(panorama_report.report_json))
    probe_c_payload = _parse_report_json(probe_c_report.report_json)
    probe_c_data = probe_c_payload.get("data") if isinstance(probe_c_payload.get("data"), dict) else {}

    return {
        "report_type": "XIAOHEBAO_RISK",
        "title": "小荷包风险报告",
        "query_time": datetime.now().isoformat(timespec="seconds"),
        "cache_days": min(int(getattr(settings, "RISK_REPORT_CACHE_DAYS", 14) or 14), 14),
        "user_profile": {
            "user_id": user.id,
            "name": user.name,
            "phone": user.phone,
            "id_card": user.id_card_num,
            "id_address": user.id_address,
            "created_at": _dt(user.created_at),
            "real_name_status": user.real_name_status,
            "face_auth_status": user.face_auth_status,
            "ocr_submitted_at": _dt(user.ocr_submitted_at),
            "application_submitted_at": _dt(user.application_submitted_at),
            "last_login_at": _dt(user.last_login_at),
        },
        "system_risk": {
            "blacklist_hit": bool(user.blacklist_hit),
            "blacklist_reason": user.blacklist_reason,
            "blacklist_checked_at": _dt(user.blacklist_checked_at),
            "active_blacklist_entries": [_serialize_blacklist_item(item) for item in active_blacklist],
            "risk_list_hit": bool(getattr(user, "risk_list_hit", False)),
            "risk_list_source": getattr(user, "risk_list_source", None),
            "risk_list_reason": getattr(user, "risk_list_reason", None),
            "risk_list_checked_at": _dt(getattr(user, "risk_list_checked_at", None)),
            "location_risk_hit": location_risk["hit"],
            "location_risk_keywords": location_risk["keywords"],
            "location_risk_detail": location_risk["detail"],
            "login_location_blocked": bool(user.location_risk_blocked),
            "login_location_reason": user.location_risk_reason,
            "login_location_at": _dt(user.location_risk_at),
            "same_phone_binding_count": len(phone_bindings),
            "phone_bindings": [_serialize_phone_binding(item) for item in phone_bindings],
        },
        "latest_order": _serialize_latest_order(latest_loan) if latest_loan else None,
        "recent_access": [_serialize_event(item) for item in recent_events],
        "panorama": {
            "report_id": panorama_report.id,
            "source": panorama_report.source,
            "query_time": _dt(panorama_report.query_time),
            "payload": panorama_payload,
        },
        "probe_c": {
            "report_id": probe_c_report.id,
            "source": probe_c_report.source,
            "query_time": _dt(probe_c_report.query_time),
            "result_label": _probe_result_label(probe_c_data.get("result_code")),
            "payload": probe_c_payload,
        },
    }


def _append_location_text(parts: list[str], *values: Optional[str]) -> None:
    """追加非空地址文本。

    :param parts: 地址片段列表
    :param values: 地址字段
    :return: 无返回值
    """
    for value in values:
        text = (value or "").strip()
        if text:
            parts.append(text)


def _is_overseas_country(country: Optional[str]) -> bool:
    """判断国家字段是否属于中国大陆境外。

    :param country: 国家或地区名称
    :return: 是否命中境外风险
    """
    text = (country or "").strip()
    if not text:
        return False
    if text in MAINLAND_COUNTRY_NAMES:
        return False
    return "中国" not in text or "香港" in text or "澳门" in text or "台湾" in text


def _resolve_user_location_risk(user: Optional[User], events: list[UserEvent]) -> Dict[str, Any]:
    """根据用户GPS、IP和身份证地址判断是否命中风险地区。

    :param user: 用户对象
    :param events: 用户访问日志
    :return: 风险命中摘要
    """
    parts: list[str] = []
    overseas_hit = False
    if user:
        _append_location_text(
            parts,
            user.location_province,
            user.location_city,
            user.location_district,
            user.location_street,
            user.location_address,
            user.id_address,
        )
    for event in events:
        _append_location_text(
            parts,
            event.ip_province,
            event.ip_city,
            event.ip_district,
            event.ip_detail,
            event.lon_lat_province,
            event.lon_lat_city,
            event.lon_lat_district,
            event.lon_lat_detail,
        )
        overseas_hit = overseas_hit or _is_overseas_country(event.ip_country)
        overseas_hit = overseas_hit or _is_overseas_country(event.lon_lat_country)

    combined_text = " ".join(parts)
    keywords = [keyword for keyword in RISK_LOCATION_KEYWORDS if keyword in combined_text]
    if overseas_hit or RISK_LOCATION_OVERSEAS_KEYWORD in combined_text:
        keywords.append(RISK_LOCATION_OVERSEAS_KEYWORD)
    unique_keywords = list(dict.fromkeys(keywords))
    return {
        "hit": bool(unique_keywords),
        "keywords": unique_keywords,
        "detail": "命中风险位置：" + "、".join(unique_keywords) if unique_keywords else "",
    }


def _serialize_latest_order(loan: Loan) -> Dict[str, Any]:
    """序列化综合报告中的最近订单摘要。

    :param loan: 订单对象
    :return: 订单摘要
    """
    payload = serialize_loan_snapshot(loan, include_user=True)
    payload["remaining_repayment_amount"] = calculate_remaining_repayment_amount(loan)
    return payload


def _parse_report_json(value: Any) -> Dict[str, Any]:
    """解析报告JSON。

    :param value: JSON文本或对象
    :return: 字典
    """
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _strip_panorama_credit_detail(value: Dict[str, Any]) -> Dict[str, Any]:
    """移除全景雷达报告中的信用详情字段。

    :param value: 全景雷达报告JSON
    :return: 不包含信用详情字段的报告JSON
    """
    payload = json.loads(json.dumps(value or {}, ensure_ascii=False, default=_json_default))
    if isinstance(payload.get("data"), dict):
        payload["data"].pop("current_report_detail", None)
    payload.pop("current_report_detail", None)
    return payload


def _normalize_xiaohebao_report_json(value: Any) -> str:
    """规范化旧缓存报告为小荷包风险报告输出格式。

    :param value: 报告JSON文本或对象
    :return: 规范化后的JSON文本
    """
    payload = _parse_report_json(value)
    payload["report_type"] = "XIAOHEBAO_RISK"
    payload["title"] = "小荷包风险报告"
    if isinstance(payload.get("panorama"), dict):
        payload["panorama"]["payload"] = _strip_panorama_credit_detail(payload["panorama"].get("payload") or {})
    return json.dumps(payload, ensure_ascii=False, default=_json_default)


def _is_probe_c_composite_payload(value: Any) -> bool:
    """判断综合报告缓存是否已经使用探针C。

    :param value: 综合报告JSON
    :return: 是否为探针C报告
    """
    payload = _parse_report_json(value)
    probe_c = payload.get("probe_c") if isinstance(payload.get("probe_c"), dict) else {}
    if probe_c.get("source") == RISK_SOURCE_PROBE_C:
        return True
    # 切换前短暂兼容：若旧字段承载的是探针C，也视为可用缓存。
    legacy_probe = payload.get("probe_a") if isinstance(payload.get("probe_a"), dict) else {}
    return legacy_probe.get("source") == RISK_SOURCE_PROBE_C


def _dt(value: Any) -> Optional[str]:
    """格式化时间。

    :param value: 时间对象
    :return: ISO时间字符串
    """
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    return None


def _json_default(value: Any) -> str:
    """转换JSON默认不支持的对象。

    :param value: 待转换对象
    :return: 可写入JSON的文本
    """
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _probe_result_label(code: Any) -> str:
    """转换探针结果编码。

    :param code: 探针结果编码
    :return: 结果文案
    """
    return {
        "1": "逾期未还款",
        "2": "正常履约",
        "3": "逾期后已还款",
        "4": "无法确认",
    }.get(str(code or ""), "未知")


def _serialize_blacklist_item(item: BlacklistEntry) -> Dict[str, Any]:
    """序列化黑名单记录。

    :param item: 黑名单记录
    :return: 黑名单摘要
    """
    return {
        "id": item.id,
        "source": item.source,
        "reason": item.reason,
        "created_by": item.created_by,
        "created_at": _dt(item.created_at),
    }


def _serialize_phone_binding(item: UserPhoneBinding) -> Dict[str, Any]:
    """序列化手机号绑定记录。

    :param item: 绑定记录
    :return: 绑定摘要
    """
    return {
        "id": item.id,
        "user_id": item.user_id,
        "bind_type": item.bind_type,
        "note": item.note,
        "bound_at": _dt(item.bound_at),
        "unbound_at": _dt(item.unbound_at),
    }


def _serialize_event(item: UserEvent) -> Dict[str, Any]:
    """序列化最近访问和操作记录。

    :param item: 用户事件
    :return: 事件摘要
    """
    return {
        "id": item.id,
        "loan_id": item.loan_id,
        "actor_type": item.actor_type,
        "event_type": item.event_type,
        "title": item.title,
        "detail": item.detail,
        "ip": item.ip,
        "ip_address": " ".join(filter(None, [item.ip_country, item.ip_province, item.ip_city, item.ip_district])),
        "lon_lat": item.lon_lat,
        "lon_lat_address": " ".join(filter(None, [item.lon_lat_country, item.lon_lat_province, item.lon_lat_city, item.lon_lat_district])),
        "created_at": _dt(item.created_at),
    }
