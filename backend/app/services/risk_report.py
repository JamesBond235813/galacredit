import copy
import hashlib
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.risk_report import RiskControlReport
from app.models.user import User
from app.services.risk_report_mock import MOCK_RISK_REPORT

RISK_SOURCE_PANORAMA = "PANORAMA"
RISK_SOURCE_PROBE_A = "PROBE_A"
RISK_SOURCE_PROBE_C = "PROBE_C"
RISK_SOURCE_MOCK = "MOCK"
PANORAMA_PRODUCT_NO = "JX1000020"
PROBE_A_PRODUCT_NO = "JX1000022"
PROBE_C_PRODUCT_NO = "JX1000021"
EMPTY_RESULT_MESSAGES = ("查询为空", "查询数据为空", "无查询结果", "暂无数据")


def serialize_risk_report(report: RiskControlReport) -> Dict[str, Any]:
    return {
        "id": report.id,
        "user_id": report.user_id,
        "name": report.name,
        "id_card": report.id_card,
        "phone": report.phone,
        "source": report.source,
        "report_json": report.report_json,
        "query_time": report.query_time,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


async def get_user_for_risk_report_async(db: AsyncSession, user_id: int) -> User:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not user.name or not user.id_card_num or not user.phone:
        raise HTTPException(status_code=400, detail="该用户实名信息不完整，无法查询风控报告")
    return user


async def get_cached_risk_report_async(db: AsyncSession, *, name: str, id_card: str) -> Optional[RiskControlReport]:
    cache_days = min(int(getattr(settings, "RISK_REPORT_CACHE_DAYS", 14) or 14), 14)
    cache_start = datetime.now() - timedelta(days=cache_days)
    stmt = select(RiskControlReport).where(
        RiskControlReport.name == name,
        RiskControlReport.id_card == id_card,
        RiskControlReport.query_time >= cache_start,
    )
    if settings.RISK_PANORAMA_ENABLED and _has_panorama_credentials():
        stmt = stmt.where(RiskControlReport.source == RISK_SOURCE_PANORAMA)
    stmt = stmt.order_by(RiskControlReport.query_time.desc())
    return (await db.execute(stmt)).scalars().first()


async def get_cached_risk_report_by_source_async(
    db: AsyncSession,
    *,
    name: str,
    id_card: str,
    source: str,
) -> Optional[RiskControlReport]:
    """按数据源获取14天内的风控报告缓存。

    :param db: 异步数据库会话
    :param name: 姓名
    :param id_card: 身份证号
    :param source: 报告来源
    :return: 缓存报告
    """
    cache_days = min(int(getattr(settings, "RISK_REPORT_CACHE_DAYS", 14) or 14), 14)
    cache_start = datetime.now() - timedelta(days=cache_days)
    stmt = (
        select(RiskControlReport)
        .where(
            RiskControlReport.name == name,
            RiskControlReport.id_card == id_card,
            RiskControlReport.source == source,
            RiskControlReport.query_time >= cache_start,
        )
        .order_by(RiskControlReport.query_time.desc())
    )
    return (await db.execute(stmt)).scalars().first()


async def get_or_create_risk_report_async(
    db: AsyncSession,
    *,
    name: str,
    id_card: str,
    phone: str,
    user_id: Optional[int] = None,
) -> RiskControlReport:
    cached_report = await get_cached_risk_report_async(db, name=name, id_card=id_card)
    if cached_report:
        return cached_report

    report_payload, source = await fetch_risk_report_payload(name=name, id_card=id_card, phone=phone)
    now = datetime.now()
    report = RiskControlReport(
        user_id=user_id,
        name=name,
        id_card=id_card,
        phone=phone,
        source=source,
        report_json=json.dumps(report_payload, ensure_ascii=False),
        query_time=now,
        created_at=now,
        updated_at=now,
    )
    db.add(report)
    await db.flush()
    return report


async def get_or_create_probe_a_report_async(
    db: AsyncSession,
    *,
    name: str,
    id_card: str,
    phone: str,
    user_id: Optional[int] = None,
) -> RiskControlReport:
    """获取或创建探针A报告。

    :param db: 异步数据库会话
    :param name: 姓名
    :param id_card: 身份证号
    :param phone: 手机号
    :param user_id: 用户ID
    :return: 探针A报告
    """
    cached_report = await get_cached_risk_report_by_source_async(
        db,
        name=name,
        id_card=id_card,
        source=RISK_SOURCE_PROBE_A,
    )
    if cached_report:
        return cached_report

    if settings.RISK_PROBE_A_ENABLED and _has_panorama_credentials():
        report_payload = await fetch_jx_product_report_async(
            name=name,
            id_card=id_card,
            phone=phone,
            product_no=PROBE_A_PRODUCT_NO,
        )
        source = RISK_SOURCE_PROBE_A
    else:
        report_payload = build_mock_probe_a_report()
        source = RISK_SOURCE_PROBE_A

    now = datetime.now()
    report = RiskControlReport(
        user_id=user_id,
        name=name,
        id_card=id_card,
        phone=phone,
        source=source,
        report_json=json.dumps(report_payload, ensure_ascii=False),
        query_time=now,
        created_at=now,
        updated_at=now,
    )
    db.add(report)
    await db.flush()
    return report


async def get_or_create_probe_c_report_async(
    db: AsyncSession,
    *,
    name: str,
    id_card: str,
    phone: str,
    user_id: Optional[int] = None,
) -> RiskControlReport:
    """获取或创建探针C报告。

    :param db: 异步数据库会话
    :param name: 姓名
    :param id_card: 身份证号
    :param phone: 手机号
    :param user_id: 用户ID
    :return: 探针C报告
    """
    cached_report = await get_cached_risk_report_by_source_async(
        db,
        name=name,
        id_card=id_card,
        source=RISK_SOURCE_PROBE_C,
    )
    if cached_report:
        return cached_report

    if settings.RISK_PROBE_C_ENABLED and _has_panorama_credentials():
        report_payload = await fetch_jx_product_report_async(
            name=name,
            id_card=id_card,
            phone=phone,
            product_no=PROBE_C_PRODUCT_NO,
        )
    else:
        report_payload = build_mock_probe_c_report()

    now = datetime.now()
    report = RiskControlReport(
        user_id=user_id,
        name=name,
        id_card=id_card,
        phone=phone,
        source=RISK_SOURCE_PROBE_C,
        report_json=json.dumps(report_payload, ensure_ascii=False),
        query_time=now,
        created_at=now,
        updated_at=now,
    )
    db.add(report)
    await db.flush()
    return report


async def fetch_risk_report_payload(*, name: str, id_card: str, phone: str) -> tuple[Dict[str, Any], str]:
    if settings.RISK_PANORAMA_ENABLED and _has_panorama_credentials():
        return await fetch_panorama_report_async(name=name, id_card=id_card, phone=phone), RISK_SOURCE_PANORAMA
    return build_mock_risk_report(), RISK_SOURCE_MOCK


async def fetch_panorama_report_async(*, name: str, id_card: str, phone: str) -> Dict[str, Any]:
    return await fetch_jx_product_report_async(
        name=name,
        id_card=id_card,
        phone=phone,
        product_no=PANORAMA_PRODUCT_NO,
    )


async def fetch_jx_product_report_async(*, name: str, id_card: str, phone: str, product_no: str) -> Dict[str, Any]:
    """调用极信指定产品风控报告。

    :param name: 姓名
    :param id_card: 身份证号
    :param phone: 手机号
    :param product_no: 产品编号
    :return: 风控接口响应
    """
    timestamp = int(time.time() * 1000)
    access_key = settings.RISK_PANORAMA_ACCESS_KEY
    secret_key = settings.RISK_PANORAMA_SECRET_KEY
    sign = hashlib.md5(f"{timestamp}{access_key}{secret_key}".encode("utf-8")).hexdigest()

    body_json = json.dumps(
        {
            "name": name,
            "phone": phone,
            "idNumber": id_card,
            "productNo": product_no,
        },
        ensure_ascii=False,
    )
    payload = {
        "timestamp": timestamp,
        "requestId": f"{uuid.uuid4().hex}{timestamp}",
        "sign": sign,
        "version": "1",
        "accesssKey": access_key,
        "merchantNo": settings.RISK_PANORAMA_MERCHANT_NO,
        "body": body_json,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                settings.RISK_PANORAMA_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            response_text = response.text
    except httpx.HTTPStatusError as exc:
        error_body = exc.response.text
        raise HTTPException(status_code=502, detail=f"风控服务请求失败：{error_body or exc}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="风控服务连接失败，请稍后重试") from exc

    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="风控服务返回格式异常") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="风控服务返回格式异常")

    code = payload.get("code")
    if code not in {200, "200", None}:
        message = payload.get("message") or payload.get("msg") or "风控服务返回失败"
        if _is_empty_risk_result_message(message):
            return _build_empty_risk_result_payload(payload, product_no=product_no, message=str(message))
        raise HTTPException(status_code=502, detail=str(message))

    return payload


def _is_empty_risk_result_message(message: Any) -> bool:
    """判断风控接口返回是否属于无记录结果。

    :param message: 风控接口消息
    :return: 是否为无记录结果
    """
    text = str(message or "").strip()
    return any(keyword in text for keyword in EMPTY_RESULT_MESSAGES)


def _build_empty_risk_result_payload(payload: Dict[str, Any], *, product_no: str, message: str) -> Dict[str, Any]:
    """把风控无记录结果转换成可存储的报告片段。

    :param payload: 原始风控响应
    :param product_no: 产品编号
    :param message: 风控接口消息
    :return: 标准化后的空报告
    """
    normalized = dict(payload or {})
    normalized["code"] = 200
    normalized["message"] = message
    normalized["productNo"] = product_no
    normalized["empty_result"] = True
    normalized["data"] = normalized.get("data") if isinstance(normalized.get("data"), dict) else {}
    return normalized


def build_mock_probe_a_report() -> Dict[str, Any]:
    return {
        "code": 200,
        "message": "success",
        "requestId": f"{uuid.uuid4().hex}{int(time.time() * 1000)}",
        "timestamp": int(time.time() * 1000),
        "responseId": uuid.uuid4().hex,
        "data": {
            "result_code": "3",
            "max_overdue_amt": "(1000,2000]",
            "max_overdue_days": "[16,30]",
            "latest_overdue_time": "2025-12",
            "currently_overdue": "0",
            "currently_performance": "3",
            "acc_exc": "1",
            "acc_sleep": "2",
        },
    }


def build_mock_probe_c_report() -> Dict[str, Any]:
    """构建探针C模拟报告。

    :return: 探针C模拟响应
    """
    return {
        "code": 200,
        "message": "success",
        "requestId": f"{uuid.uuid4().hex}{int(time.time() * 1000)}",
        "timestamp": int(time.time() * 1000),
        "responseId": uuid.uuid4().hex,
        "data": {
            "result_code": "2",
            "max_performance_amt": "1000-2000",
            "latest_performance_time": "2026-05",
            "count_performance": "5",
            "currently_overdue": "0",
            "currently_performance": "4",
            "acc_exc": "0",
            "acc_sleep": "7",
        },
    }


def build_mock_risk_report() -> Dict[str, Any]:
    payload = copy.deepcopy(MOCK_RISK_REPORT)
    payload["requestId"] = f"{uuid.uuid4().hex}{int(time.time() * 1000)}"
    payload["timestamp"] = int(time.time() * 1000)
    payload["responseId"] = uuid.uuid4().hex
    return payload


def _has_panorama_credentials() -> bool:
    return all(
        [
            settings.RISK_PANORAMA_API_URL,
            settings.RISK_PANORAMA_MERCHANT_NO,
            settings.RISK_PANORAMA_ACCESS_KEY,
            settings.RISK_PANORAMA_SECRET_KEY,
        ]
    )
