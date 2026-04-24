import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.channel import ChannelLandingResponse
from app.schemas.user import LoginRequest, SendCodeRequest, Token
from app.services.audit import log_user_event_async
from app.services.channel_service import (
    bind_user_source_channel_async,
    get_channel_by_name_async,
    serialize_channel_landing,
)
from app.services.loan_flow import get_or_create_loan_async

router = APIRouter()

MOCK_CODES = {}


@router.post("/send-code")
async def send_code(req: SendCodeRequest):
    code = f"{random.randint(1000, 9999)}"
    MOCK_CODES[req.phone] = code
    return {"msg": "验证码发送成功", "code": code}


@router.get("/channels/{channel_name}", response_model=ChannelLandingResponse)
async def get_channel_entry(channel_name: str, db: AsyncSession = Depends(get_async_db)):
    channel = await get_channel_by_name_async(db, channel_name, active_only=True)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道链接不存在或已停用")
    return serialize_channel_landing(channel)


@router.post("/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    real_code = MOCK_CODES.get(req.phone)
    if not real_code or req.code != real_code:
        raise HTTPException(status_code=400, detail="验证码错误或已失效")

    now = datetime.utcnow()
    channel = None
    if req.channel_name:
        channel = await get_channel_by_name_async(db, req.channel_name, active_only=True)
        if not channel:
            raise HTTPException(status_code=400, detail="渠道链接不存在或已停用")

    user = (await db.execute(select(User).where(User.phone == req.phone))).scalar_one_or_none()
    is_new_user = user is None

    if user is None:
        user = User(phone=req.phone, face_auth_status="PENDING")
        db.add(user)
        await db.flush()

    loan = await get_or_create_loan_async(db, user.id)

    user.last_login_at = now
    attribution_status = (
        await bind_user_source_channel_async(db, user=user, channel=channel, loan=loan)
        if channel
        else None
    )

    if is_new_user:
        await log_user_event_async(
            db,
            user=user,
            loan=loan,
            actor_type="SYSTEM",
            event_type="REGISTER",
            title="新用户注册",
            detail=(
                f"手机号 {user.phone} 首次登录，系统自动创建用户及初始订单。"
                f"{f' 归因渠道：{channel.sales_name}（{channel.channel_name}）。' if channel else ''}"
            ),
        )

    login_detail = "H5 登录成功。"
    if channel and attribution_status in {"BOUND", "REFRESHED"}:
        login_detail += f" 入口渠道：{channel.sales_name}（{channel.channel_name}）。"

    await log_user_event_async(
        db,
        user=user,
        loan=loan,
        actor_type="USER",
        event_type="LOGIN",
        title="用户登录",
        detail=login_detail,
    )

    await db.commit()
    MOCK_CODES.pop(req.phone, None)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.phone, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
