from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Request
from jose import JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BizException
from app.core.database import get_async_db
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.oauth_client import OAuthClient
from app.models.oauth_token import OAuthToken
from app.models.user import User
from app.models.user_event import UserEvent
from app.schemas.channel import ChannelLandingResponse
from app.schemas.user import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    SendCodeRequest,
    SliderCaptchaCreateRequest,
    SliderCaptchaCreateResponse,
    SliderCaptchaVerifyRequest,
    SliderCaptchaVerifyResponse,
    SmsLoginRequest,
    Token,
)
from app.api.req_util import resolve_client_ip
from app.services.password_login_guard import PasswordLoginGuard
from app.services.sms_auth import SmsAuthManager
from app.services.sms_service import sms_service
from app.services.slider_captcha import SliderCaptchaManager
from app.services.audit import log_user_event_async
from app.services.blacklist_service import refresh_user_blacklist_status
from app.services.ip_geo import resolve_ip_geo
from app.services.login_location_risk import apply_login_location
from app.services.risk_list_service import refresh_user_risk_list_status
from app.services.channel_service import (
    bind_user_source_channel_async,
    get_channel_by_invite_code_async,
    get_channel_by_name_async,
    serialize_channel_landing,
)

router = APIRouter()

sms_auth_manager = SmsAuthManager(
    phone_cooldown_seconds=settings.SMS_PHONE_COOLDOWN_SECONDS,
    ip_rate_limit_per_minute=settings.SMS_IP_RATE_LIMIT_PER_MINUTE,
    code_expire_seconds=settings.SMS_CODE_EXPIRE_SECONDS,
    mock_enabled=settings.SMS_CODE_MOCK_ENABLED,
    mock_code=settings.SMS_MOCK_CODE,
)

password_login_guard = PasswordLoginGuard(
    max_attempts=settings.PASSWORD_LOGIN_MAX_ATTEMPTS,
    window_seconds=settings.PASSWORD_LOGIN_WINDOW_SECONDS,
    freeze_seconds=settings.PASSWORD_LOGIN_FREEZE_SECONDS,
)

slider_captcha_manager = SliderCaptchaManager(
    tolerance_px=settings.CAPTCHA_SLIDER_TOLERANCE_PX,
    min_elapsed_ms=settings.CAPTCHA_SLIDER_MIN_ELAPSED_MS,
    challenge_expire_seconds=settings.CAPTCHA_SLIDER_CHALLENGE_EXPIRE_SECONDS,
    challenge_max_fails=settings.CAPTCHA_SLIDER_CHALLENGE_MAX_FAILS,
    ticket_expire_seconds=settings.CAPTCHA_SLIDER_TICKET_EXPIRE_SECONDS,
    min_width=settings.CAPTCHA_SLIDER_MIN_WIDTH,
    max_width=settings.CAPTCHA_SLIDER_MAX_WIDTH,
    height=settings.CAPTCHA_SLIDER_HEIGHT,
    block_size=settings.CAPTCHA_SLIDER_BLOCK_SIZE,
)

_sms_code_audit_cache: Dict[str, dict] = {}
_SMS_CODE_AUDIT_CACHE_SECONDS = 600


def _build_login_frozen_message(remain_minutes: int) -> str:
    """构建登录冻结文案。

    :param remain_minutes: 剩余冻结分钟
    :return: 提示文案
    """
    return f"由于密码输入错误次数过多，请在{max(int(remain_minutes), 1)}分钟后再输入密码。"


async def _upsert_oauth_client(db: AsyncSession, client_id: str) -> None:
    """写入或更新客户端信息。

    :param db: 异步数据库会话
    :param client_id: 客户端标识
    :return: None
    """
    client = (await db.execute(select(OAuthClient).where(OAuthClient.client_id == client_id))).scalar_one_or_none()
    if client is None:
        db.add(OAuthClient(client_id=client_id, client_name=client_id, is_active=True))
        return
    client.is_active = True
    client.updated_at = datetime.now()


async def _save_token_pair(
    db: AsyncSession,
    user: User,
    client_id: str,
    access_jti: str,
    refresh_jti: str,
    access_token: str,
    refresh_token: str,
    access_expires_at: datetime,
    refresh_expires_at: datetime,
) -> None:
    """持久化 token 并吊销同客户端旧 token。

    :param db: 异步数据库会话
    :param user: 用户对象
    :param client_id: 客户端标识
    :param access_jti: access token jti
    :param refresh_jti: refresh token jti
    :param access_token: access token 字符串
    :param refresh_token: refresh token 字符串
    :param access_expires_at: access token 过期时间
    :param refresh_expires_at: refresh token 过期时间
    :return: None
    """
    now = datetime.now()
    await db.execute(
        update(OAuthToken)
        .where(
            OAuthToken.user_id == user.id,
            OAuthToken.client_id == client_id,
            OAuthToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    db.add(
        OAuthToken(
            user_id=user.id,
            phone=user.phone,
            client_id=client_id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )
    )


def _trim_auth_audit_cache(now: datetime) -> None:
    """清理过期的验证码审查缓存。

    :param now: 当前时间
    :return: None
    """
    expired_phones = [
        phone
        for phone, item in _sms_code_audit_cache.items()
        if (now - item.get("created_at", now)).total_seconds() > _SMS_CODE_AUDIT_CACHE_SECONDS
    ]
    for phone in expired_phones:
        _sms_code_audit_cache.pop(phone, None)


async def _build_ip_geo_payload(ip: str) -> dict:
    """构建 IP 审查字段。

    :param ip: 客户端 IP
    :return: IP 与归属地字段
    """
    geo = await resolve_ip_geo(ip)
    return {
        "ip": ip or "",
        "ip_country": geo.get("country", ""),
        "ip_province": geo.get("province", ""),
        "ip_city": geo.get("city", ""),
        "ip_district": geo.get("district", ""),
        "ip_detail": geo.get("detail", ""),
    }


def _record_auth_ip_event(
    db: AsyncSession,
    user: User,
    event_type: str,
    title: str,
    detail: str,
    ip_payload: dict,
    created_at: Optional[datetime] = None,
) -> None:
    """写入认证链路 IP 审查事件。

    :param db: 异步数据库会话
    :param user: 用户对象
    :param event_type: 事件类型
    :param title: 事件标题
    :param detail: 事件详情
    :param ip_payload: IP 与归属地字段
    :param created_at: 事件发生时间
    :return: None
    """
    db.add(
        UserEvent(
            user_id=user.id,
            loan_id=None,
            actor_type="USER",
            event_type=event_type,
            title=title,
            detail=detail,
            ip=ip_payload.get("ip", ""),
            ip_country=ip_payload.get("ip_country", ""),
            ip_province=ip_payload.get("ip_province", ""),
            ip_city=ip_payload.get("ip_city", ""),
            ip_district=ip_payload.get("ip_district", ""),
            ip_detail=ip_payload.get("ip_detail", ""),
            created_at=created_at or datetime.now(),
        )
    )


async def _remember_sms_code_audit(db: AsyncSession, phone: str, ip: str, created_at: datetime) -> None:
    """记录或暂存验证码发送 IP 审查事件。

    :param db: 异步数据库会话
    :param phone: 手机号
    :param ip: 客户端 IP
    :param created_at: 验证码发送时间
    :return: None
    """
    _trim_auth_audit_cache(created_at)
    ip_payload = await _build_ip_geo_payload(ip)
    detail = "页面：登录；空间：短信验证码；操作：发送验证码成功；接口：POST /api/auth/send-code"
    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    logged = False
    if user is not None:
        _record_auth_ip_event(
            db=db,
            user=user,
            event_type="SMS_CODE_SEND",
            title="发送短信验证码",
            detail=detail,
            ip_payload=ip_payload,
            created_at=created_at,
        )
        logged = True
    # 登录前新用户尚无 user_id，先暂存，短信登录创建用户后再补写到用户审查日志。
    _sms_code_audit_cache[phone] = {
        "ip_payload": ip_payload,
        "created_at": created_at,
        "detail": detail,
        "logged": logged,
    }


def _bind_pending_sms_code_audit(db: AsyncSession, user: User, now: datetime) -> None:
    """将登录前暂存的验证码发送事件绑定到用户。

    :param db: 异步数据库会话
    :param user: 用户对象
    :param now: 当前时间
    :return: None
    """
    _trim_auth_audit_cache(now)
    pending = _sms_code_audit_cache.get(user.phone)
    if not pending or pending.get("logged"):
        return
    _record_auth_ip_event(
        db=db,
        user=user,
        event_type="SMS_CODE_SEND",
        title="发送短信验证码",
        detail=pending.get("detail", ""),
        ip_payload=pending.get("ip_payload", {}),
        created_at=pending.get("created_at") or now,
    )
    pending["logged"] = True


@router.post("/send-code")
async def send_code(req: SendCodeRequest, request: Request, db: AsyncSession = Depends(get_async_db)):
    """下发短信验证码（支持 mock 模式）。

    :param req: 下发短信请求体
    :param request: FastAPI 请求对象
    :return: 下发结果与冷却秒数
    """
    captcha_ok = await slider_captcha_manager.consume_ticket(req.phone, req.captcha_ticket)
    if not captcha_ok:
        raise BizException("图形验证码校验失败或已过期", code=400)

    client_ip = resolve_client_ip(request)
    success, remain = await sms_auth_manager.issue_code(phone=req.phone, ip=client_ip)
    if not success:
        raise BizException(f"发送过于频繁，请{remain}秒后重试", code=429)

    sms_ok, cooldown_seconds, message = await sms_service.send_code(phone=req.phone, biz_type="LOGIN")
    if not sms_ok:
        raise BizException(message, code=400)
    await _remember_sms_code_audit(db, req.phone, client_ip, datetime.now())
    await db.commit()
    return {"msg": "验证码发送成功", "cooldown_seconds": cooldown_seconds}


@router.post("/slider-captcha/create", response_model=SliderCaptchaCreateResponse)
async def create_slider_captcha(req: SliderCaptchaCreateRequest):
    payload = await slider_captcha_manager.create_challenge(width=req.width)
    return payload


@router.post("/slider-captcha/verify", response_model=SliderCaptchaVerifyResponse)
async def verify_slider_captcha(req: SliderCaptchaVerifyRequest):
    try:
        ticket = await slider_captcha_manager.verify_challenge(
            phone=req.phone,
            captcha_id=req.captcha_id,
            offset_x=req.offset_x,
            elapsed_ms=req.elapsed_ms,
        )
    except ValueError as error:
        raise BizException(str(error), code=400) from error
    return {"captcha_ticket": ticket, "expires_seconds": settings.CAPTCHA_SLIDER_TICKET_EXPIRE_SECONDS}


@router.get("/channels/{channel_name}", response_model=ChannelLandingResponse)
async def get_channel_entry(channel_name: str, db: AsyncSession = Depends(get_async_db)):
    channel = await get_channel_by_name_async(db, channel_name, active_only=True)
    if not channel:
        raise BizException("渠道链接不存在或已停用", code=404)
    return serialize_channel_landing(channel)


@router.get("/channel-invites/{invite_code}", response_model=ChannelLandingResponse)
async def get_channel_invite_entry(invite_code: str, db: AsyncSession = Depends(get_async_db)):
    """校验每日动态渠道码。

    :param invite_code: 每日动态渠道码
    :param db: 异步数据库会话
    :return: 渠道落地页信息
    """
    channel = await get_channel_by_invite_code_async(db, invite_code, active_only=True)
    if not channel:
        raise BizException("渠道链接不存在或已停用", code=404)
    return serialize_channel_landing(channel)


@router.post("/login", response_model=Token)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_async_db)):
    """手机号密码登录。

    :param req: 登录请求体
    :param request: FastAPI 请求对象
    :param db: 异步数据库会话
    :return: access token 与 refresh token
    """
    frozen_minutes = await password_login_guard.before_verify(req.phone)
    if frozen_minutes > 0:
        raise BizException(_build_login_frozen_message(frozen_minutes), code=401)

    client_id = request.headers.get("client-id", "h5-web").strip() or "h5-web"
    now = datetime.now()
    channel = None
    if req.channel_name:
        channel = await get_channel_by_name_async(db, req.channel_name, active_only=True)
        if not channel:
            raise BizException("渠道链接不存在或已停用", code=400)

    user = (await db.execute(select(User).where(User.phone == req.phone))).scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        frozen_minutes = await password_login_guard.on_failure(req.phone)
        if frozen_minutes > 0:
            raise BizException(_build_login_frozen_message(frozen_minutes), code=401)
        raise BizException("用户或密码不正确", code=401)

    await password_login_guard.on_success(req.phone)
    if req.latitude is not None and req.longitude is not None:
        try:
            await apply_login_location(
                db,
                user,
                latitude=req.latitude,
                longitude=req.longitude,
                accuracy=req.accuracy,
                fallback_ip=resolve_client_ip(request, default_ip=""),
            )
        except ValueError as exc:
            await db.commit()
            raise BizException(str(exc), code=403) from exc
    user.last_login_at = now
    await refresh_user_blacklist_status(db, user)
    await refresh_user_risk_list_status(db, user)
    attribution_status = (
        await bind_user_source_channel_async(db, user=user, channel=channel, loan=None)
        if channel
        else None
    )

    login_detail = "H5 登录成功。"
    if channel and attribution_status in {"BOUND", "REFRESHED"}:
        login_detail += f" 入口渠道：{channel.sales_name}（{channel.channel_name}）。"

    await log_user_event_async(
        db,
        user=user,
        loan=None,
        actor_type="USER",
        event_type="LOGIN",
        title="用户登录",
        detail=login_detail,
    )
    await _upsert_oauth_client(db, client_id)

    token_payload = await _issue_user_token_pair(db=db, user=user, client_id=client_id, now=now)
    await db.commit()
    return token_payload


@router.post("/sms-login", response_model=Token)
async def sms_login(req: SmsLoginRequest, request: Request, db: AsyncSession = Depends(get_async_db)):
    client_id = request.headers.get("client-id", "h5-web").strip() or "h5-web"
    now = datetime.now()
    verified = await sms_service.verify_code(phone=req.phone, biz_type="LOGIN", code=req.sms_code)
    if not verified:
        raise BizException("短信验证码错误或已过期", code=401)

    user = (await db.execute(select(User).where(User.phone == req.phone))).scalar_one_or_none()
    channel = None
    if req.invite_code:
        channel = await get_channel_by_invite_code_async(db, req.invite_code, active_only=True)
        if not channel:
            raise BizException("渠道链接不存在或已停用", code=400)

    if user is None:
        user = User(phone=req.phone, last_login_at=now)
        db.add(user)
        await db.flush()
        if channel:
            await bind_user_source_channel_async(db, user=user, channel=channel, loan=None)
        detail = "短信验证码登录成功（新注册用户）。"
    else:
        detail = "短信验证码登录成功。"
    if req.latitude is not None and req.longitude is not None:
        try:
            await apply_login_location(
                db,
                user,
                latitude=req.latitude,
                longitude=req.longitude,
                accuracy=req.accuracy,
                fallback_ip=resolve_client_ip(request, default_ip=""),
            )
        except ValueError as exc:
            await db.commit()
            raise BizException(str(exc), code=403) from exc
    user.last_login_at = now
    await refresh_user_blacklist_status(db, user)
    await refresh_user_risk_list_status(db, user)
    _bind_pending_sms_code_audit(db, user, now)
    login_ip_payload = await _build_ip_geo_payload(resolve_client_ip(request, default_ip=""))
    _record_auth_ip_event(
        db=db,
        user=user,
        event_type="SMS_LOGIN",
        title="短信验证码登录",
        detail=(
            "页面：登录；空间：短信验证码；操作：短信验证码登录成功；接口：POST /api/auth/sms-login；"
            f"新注册用户：{'是' if '新注册用户' in detail else '否'}"
        ),
        ip_payload=login_ip_payload,
        created_at=now,
    )

    await log_user_event_async(
        db,
        user=user,
        loan=None,
        actor_type="USER",
        event_type="LOGIN",
        title="用户登录",
        detail=detail,
    )
    await _upsert_oauth_client(db, client_id)
    token_payload = await _issue_user_token_pair(db=db, user=user, client_id=client_id, now=now)
    await db.commit()
    return token_payload


async def _issue_user_token_pair(db: AsyncSession, user: User, client_id: str, now: datetime) -> dict:
    """签发并持久化用户 token 对。

    :param db: 异步数据库会话
    :param user: 用户对象
    :param client_id: 客户端标识
    :param now: 当前时间
    :return: token 响应体
    """
    access_token_expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    access_expires_at = now + access_token_expires_delta
    refresh_expires_at = now + refresh_token_expires_delta
    access_jti = uuid4().hex
    refresh_jti = uuid4().hex
    access_token = create_access_token(
        subject=user.phone,
        expires_delta=access_token_expires_delta,
        jti=access_jti,
        client_id=client_id,
    )
    refresh_token = create_refresh_token(
        subject=user.phone,
        expires_delta=refresh_token_expires_delta,
        jti=refresh_jti,
        client_id=client_id,
    )
    await _save_token_pair(
        db=db,
        user=user,
        client_id=client_id,
        access_jti=access_jti,
        refresh_jti=refresh_jti,
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "access_token_expires_at": access_expires_at,
        "refresh_token_expires_at": refresh_expires_at,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    """使用 refresh token 刷新登录态。

    :param req: 刷新请求体
    :param db: 异步数据库会话
    :return: 新 access token 与 refresh token
    """
    credentials_exception = BizException("refresh_token 无效或已过期", code=401)
    try:
        payload = jwt.decode(req.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone = payload.get("sub")
        refresh_jti = payload.get("jti")
        token_type = payload.get("typ")
        client_id = (payload.get("cid") or "h5-web").strip() or "h5-web"
        if token_type != "refresh" or not phone or not refresh_jti:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    now = datetime.now()
    token_row = (
        await db.execute(
            select(OAuthToken).where(
                OAuthToken.refresh_jti == refresh_jti,
                OAuthToken.refresh_token == req.refresh_token,
                OAuthToken.revoked_at.is_(None),
                OAuthToken.refresh_expires_at > now,
            )
        )
    ).scalar_one_or_none()
    if token_row is None:
        raise credentials_exception

    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    if user is None:
        raise credentials_exception

    access_token_expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    access_expires_at = now + access_token_expires_delta
    refresh_expires_at = now + refresh_token_expires_delta
    access_jti = uuid4().hex
    new_refresh_jti = uuid4().hex
    access_token = create_access_token(
        subject=user.phone,
        expires_delta=access_token_expires_delta,
        jti=access_jti,
        client_id=client_id,
    )
    new_refresh_token = create_refresh_token(
        subject=user.phone,
        expires_delta=refresh_token_expires_delta,
        jti=new_refresh_jti,
        client_id=client_id,
    )

    token_row.revoked_at = now
    await _upsert_oauth_client(db, client_id)
    await _save_token_pair(
        db=db,
        user=user,
        client_id=client_id,
        access_jti=access_jti,
        refresh_jti=new_refresh_jti,
        access_token=access_token,
        refresh_token=new_refresh_token,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )
    await db.commit()
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "access_token_expires_at": access_expires_at,
        "refresh_token_expires_at": refresh_expires_at,
    }


@router.post("/logout")
async def logout(req: LogoutRequest, request: Request, db: AsyncSession = Depends(get_async_db)):
    """退出登录并吊销当前 access/refresh token。

    :param req: 登出请求体
    :param request: FastAPI 请求对象
    :param db: 异步数据库会话
    :return: 处理结果
    """
    auth_header = (request.headers.get("authorization") or "").strip()
    if not auth_header.lower().startswith("bearer "):
        return {"msg": "退出成功"}
    access_token = auth_header.split(" ", 1)[1].strip()
    if not access_token:
        return {"msg": "退出成功"}

    now = datetime.now()
    await db.execute(
        update(OAuthToken)
        .where(
            OAuthToken.access_token == access_token,
            OAuthToken.refresh_token == req.refresh_token,
            OAuthToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await db.commit()
    return {"msg": "退出成功"}
