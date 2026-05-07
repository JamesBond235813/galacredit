from uuid import uuid4
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.oauth_client import OAuthClient
from app.models.oauth_token import OAuthToken
from app.models.user import User
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
    ticket_expire_seconds=settings.CAPTCHA_SLIDER_TICKET_EXPIRE_SECONDS,
    min_width=settings.CAPTCHA_SLIDER_MIN_WIDTH,
    max_width=settings.CAPTCHA_SLIDER_MAX_WIDTH,
    height=settings.CAPTCHA_SLIDER_HEIGHT,
    block_size=settings.CAPTCHA_SLIDER_BLOCK_SIZE,
)


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


@router.post("/send-code")
async def send_code(req: SendCodeRequest, request: Request):
    """下发短信验证码（支持 mock 模式）。

    :param req: 下发短信请求体
    :param request: FastAPI 请求对象
    :return: 下发结果与冷却秒数
    """
    captcha_ok = await slider_captcha_manager.consume_ticket(req.phone, req.captcha_ticket)
    if not captcha_ok:
        raise HTTPException(status_code=400, detail="图形验证码校验失败或已过期")

    client_ip = resolve_client_ip(request)
    success, remain = await sms_auth_manager.issue_code(phone=req.phone, ip=client_ip)
    if not success:
        raise HTTPException(status_code=429, detail=f"发送过于频繁，请{remain}秒后重试")

    sms_ok, cooldown_seconds, message = await sms_service.send_code(phone=req.phone, biz_type="LOGIN")
    if not sms_ok:
        raise HTTPException(status_code=400, detail=message)
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
        raise HTTPException(status_code=400, detail=str(error))
    return {"captcha_ticket": ticket, "expires_seconds": settings.CAPTCHA_SLIDER_TICKET_EXPIRE_SECONDS}


@router.get("/channels/{channel_name}", response_model=ChannelLandingResponse)
async def get_channel_entry(channel_name: str, db: AsyncSession = Depends(get_async_db)):
    channel = await get_channel_by_name_async(db, channel_name, active_only=True)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道链接不存在或已停用")
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
        raise HTTPException(status_code=400, detail=_build_login_frozen_message(frozen_minutes))

    client_id = request.headers.get("client-id", "h5-web").strip() or "h5-web"
    now = datetime.now()
    channel = None
    if req.channel_name:
        channel = await get_channel_by_name_async(db, req.channel_name, active_only=True)
        if not channel:
            raise HTTPException(status_code=400, detail="渠道链接不存在或已停用")

    user = (await db.execute(select(User).where(User.phone == req.phone))).scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        frozen_minutes = await password_login_guard.on_failure(req.phone)
        if frozen_minutes > 0:
            raise HTTPException(status_code=400, detail=_build_login_frozen_message(frozen_minutes))
        raise HTTPException(status_code=400, detail="用户或密码不正确")

    await password_login_guard.on_success(req.phone)
    user.last_login_at = now
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
        raise HTTPException(status_code=400, detail="短信验证码错误或已过期")

    user = (await db.execute(select(User).where(User.phone == req.phone))).scalar_one_or_none()
    channel = None
    if user is None and req.invite_code:
        channel = await get_channel_by_invite_code_async(db, req.invite_code, active_only=True)

    if user is None:
        user = User(phone=req.phone, last_login_at=now)
        db.add(user)
        await db.flush()
        if channel:
            await bind_user_source_channel_async(db, user=user, channel=channel, loan=None)
        detail = "短信验证码登录成功（新注册用户）。"
    else:
        user.last_login_at = now
        detail = "短信验证码登录成功。"

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
    credentials_exception = HTTPException(status_code=401, detail="refresh_token 无效或已过期")
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
