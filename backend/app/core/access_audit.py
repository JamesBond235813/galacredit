from datetime import datetime
import logging

from fastapi import Request
from jose import JWTError, jwt
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import unquote

from app.api.req_util import resolve_client_ip
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.oauth_token import OAuthToken
from app.models.user import User
from app.models.user_event import UserEvent
from app.services.ip_geo import resolve_ip_geo

logger = logging.getLogger(__name__)


PAGE_CONTEXT = {
    "/home": "我的授信",
    "/profile": "个人中心",
    "/ocr": "实名认证",
    "/face": "人脸识别",
    "/face-mismatch": "人脸识别结果",
    "/application-form": "补充资料",
    "/review": "授信审核中",
    "/withdraw": "信用下单",
    "/bill": "付款账单",
    "/support": "客服帮助",
    "/orders": "我的订单",
    "/change-password": "修改密码",
    "/agreement": "用户协议",
    "/personal-info-authorization": "个人信息授权协议",
}


ACTION_CONTEXT = {
    ("GET", "/api/user/info"): ("页面初始化", "读取用户基础资料"),
    ("POST", "/api/user/location"): ("位置风控", "提交当前位置授权"),
    ("POST", "/api/user/ocr"): ("身份证上传区", "提交身份证正反面识别"),
    ("POST", "/api/user/face-auth"): ("人脸识别区", "提交人脸照片核验"),
    ("POST", "/api/user/application"): ("亲友联系人表单", "提交补充资料并申请授信"),
    ("POST", "/api/user/channel-bind"): ("渠道入口区", "绑定/识别专属渠道"),
    ("POST", "/api/user/change-password"): ("密码表单", "修改登录密码"),
    ("GET", "/api/loan/status"): ("额度状态区", "查看当前申请/账单状态"),
    ("GET", "/api/loan/products"): ("商品列表区", "查看可选商品"),
    ("POST", "/api/loan/order-sms-code"): ("下单确认区", "获取下单验证码"),
    ("POST", "/api/loan/withdraw"): ("下单确认区", "提交信用下单"),
    ("GET", "/api/loan/bill"): ("账单详情区", "查看还款账单"),
    ("POST", "/api/loan/repay-attempt"): ("还款操作区", "点击已还款/还款反馈"),
    ("GET", "/api/loan/ecard-secret"): ("E卡信息区", "查看E卡卡密"),
}


def _clean_header(value: str | None, max_length: int = 80) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        value = unquote(value)
    except Exception:
        pass
    return value.replace("\r", " ").replace("\n", " ")[:max_length]


def _resolve_access_context(request: Request) -> tuple[str, str]:
    page_path = _clean_header(request.headers.get("x-xhb-page-path"), 120) or _clean_header(
        request.headers.get("referer"), 160
    )
    if page_path.startswith("http"):
        try:
            from urllib.parse import urlparse

            parsed = urlparse(page_path)
            page_path = parsed.path or page_path
        except Exception:
            pass
    page_title = _clean_header(request.headers.get("x-xhb-page-title")) or PAGE_CONTEXT.get(page_path, page_path or "前端页面")
    action_space = _clean_header(request.headers.get("x-xhb-action-space"))
    action_name = _clean_header(request.headers.get("x-xhb-action-name"))

    mapped_space, mapped_action = ACTION_CONTEXT.get((request.method.upper(), request.url.path), ("服务请求", "访问服务接口"))
    action_space = action_space or mapped_space
    action_name = action_name or mapped_action

    title = f"{page_title} · {action_name}"
    detail = (
        f"页面：{page_title}（{page_path or '--'}）；"
        f"空间：{action_space}；"
        f"操作：{action_name}；"
        f"接口：{request.method.upper()} {request.url.path}"
    )
    return title, detail


class AccessAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(f"{settings.API_V1_STR}/") and request.method != "OPTIONS":
            try:
                await self._record_user_access(request)
            except Exception:
                logger.exception("record_user_access_failed path=%s method=%s", request.url.path, request.method)
        return response

    async def _record_user_access(self, request: Request) -> None:
        auth_header = (request.headers.get("authorization") or "").strip()
        if not auth_header.lower().startswith("bearer "):
            return
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return
        if payload.get("typ") != "access":
            return
        phone = payload.get("sub")
        jti = payload.get("jti")
        if not phone or not jti:
            return

        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
            if not user:
                return
            token_row = (
                await db.execute(
                    select(OAuthToken).where(
                        OAuthToken.user_id == user.id,
                        OAuthToken.access_jti == jti,
                        OAuthToken.revoked_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if not token_row:
                return

            ip = resolve_client_ip(request, default_ip="")
            geo = await resolve_ip_geo(ip)
            title, detail = _resolve_access_context(request)
            db.add(
                UserEvent(
                    user_id=user.id,
                    actor_type="USER",
                    event_type="ACCESS",
                    title=title,
                    detail=detail,
                    ip=ip,
                    ip_country=geo["country"],
                    ip_province=geo["province"],
                    ip_city=geo["city"],
                    ip_district=geo["district"],
                    ip_detail=geo["detail"],
                    created_at=datetime.now(),
                )
            )
            await db.commit()
