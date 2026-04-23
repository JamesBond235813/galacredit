import copy
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.risk_report import RiskControlReport
from app.models.user import User
from app.services.risk_report_mock import MOCK_RISK_REPORT

RISK_SOURCE_PANORAMA = "PANORAMA"
RISK_SOURCE_MOCK = "MOCK"


def serialize_risk_report(report: RiskControlReport) -> Dict[str, Any]:
    return {
        "id": report.id,
        "name": report.name,
        "id_card": report.id_card,
        "phone": report.phone,
        "source": report.source,
        "report_json": report.report_json,
        "query_time": report.query_time,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


def get_user_for_risk_report(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not user.name or not user.id_card_num or not user.phone:
        raise HTTPException(status_code=400, detail="该用户实名信息不完整，无法查询风控报告")
    return user


def get_or_create_risk_report(db: Session, *, name: str, id_card: str, phone: str) -> RiskControlReport:
    cached_report = get_cached_risk_report(db, name=name, id_card=id_card)
    if cached_report:
        return cached_report

    report_payload, source = fetch_risk_report_payload(name=name, id_card=id_card, phone=phone)
    now = datetime.utcnow()
    report = RiskControlReport(
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
    db.flush()
    return report


def get_cached_risk_report(db: Session, *, name: str, id_card: str) -> Optional[RiskControlReport]:
    thirty_days_ago = datetime.utcnow() - timedelta(days=settings.RISK_REPORT_CACHE_DAYS)
    query = db.query(RiskControlReport).filter(
        RiskControlReport.name == name,
        RiskControlReport.id_card == id_card,
        RiskControlReport.query_time >= thirty_days_ago,
    )

    if settings.RISK_PANORAMA_ENABLED and _has_panorama_credentials():
        query = query.filter(RiskControlReport.source == RISK_SOURCE_PANORAMA)

    return query.order_by(RiskControlReport.query_time.desc()).first()


def fetch_risk_report_payload(*, name: str, id_card: str, phone: str) -> tuple[Dict[str, Any], str]:
    if settings.RISK_PANORAMA_ENABLED and _has_panorama_credentials():
        return fetch_panorama_report(name=name, id_card=id_card, phone=phone), RISK_SOURCE_PANORAMA
    return build_mock_risk_report(), RISK_SOURCE_MOCK


def fetch_panorama_report(*, name: str, id_card: str, phone: str) -> Dict[str, Any]:
    timestamp = int(time.time() * 1000)
    access_key = settings.RISK_PANORAMA_ACCESS_KEY
    secret_key = settings.RISK_PANORAMA_SECRET_KEY
    sign = hashlib.md5(f"{timestamp}{access_key}{secret_key}".encode("utf-8")).hexdigest()

    body_json = json.dumps(
        {
            "name": name,
            "phone": phone,
            "idNumber": id_card,
            "productNo": "JX1000020",
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
    request_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib_request.Request(
        settings.RISK_PANORAMA_API_URL,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=30) as response:
            response_text = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=502, detail=f"风控服务请求失败：{error_body or exc.reason}") from exc
    except urllib_error.URLError as exc:
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
        raise HTTPException(status_code=502, detail=str(message))

    return payload


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
