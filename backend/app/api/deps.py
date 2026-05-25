from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_async_db
from app.models.user import User
from app.models.admin import Admin
from app.models.oauth_token import OAuthToken
from app.services.admin_session import is_admin_session_valid, normalize_admin_client_type

# H5端使用 Bearer Token 发送在 Authorization header 中
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
# 后端管理平台可以复用，或者另起一个
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/admin/login")

async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    user = await get_user_by_token_async(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_user_by_token_async(db: AsyncSession, token: str) -> User:
    """根据 JWT Token 获取 H5 用户。

    :param db: 异步数据库会话
    :param token: Bearer Token 字符串
    :return: 用户对象；无效时抛出 401
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone: str = payload.get("sub")
        access_jti: str = payload.get("jti")
        token_type: str = payload.get("typ")
        if phone is None or access_jti is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    if user is None:
        raise credentials_exception

    token_row = (
        await db.execute(
            select(OAuthToken).where(
                OAuthToken.user_id == user.id,
                OAuthToken.access_jti == access_jti,
                OAuthToken.access_token == token,
                OAuthToken.revoked_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if token_row is None:
        raise credentials_exception
    if getattr(user, "location_risk_blocked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=user.location_risk_reason or "当前登录环境存在风险，请联系客服处理",
        )
    return user


async def get_current_admin(
    db: AsyncSession = Depends(get_async_db),
    token: str = Depends(admin_oauth2_scheme),
) -> Admin:
    admin = await get_admin_by_token_async(db, token)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin


async def get_admin_by_token_async(db: AsyncSession, token: str) -> Admin:
    """根据 JWT Token 获取后台管理员。

    :param db: 异步数据库会话
    :param token: Bearer Token 字符串
    :return: 管理员对象；无效时抛出 401
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        session_id: str = payload.get("jti")
        token_type: str = payload.get("typ")
        client_type: str = normalize_admin_client_type(payload.get("cid"))
        if username is None or session_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = (await db.execute(select(Admin).where(Admin.username == username))).scalar_one_or_none()
    if admin is None:
        raise credentials_exception
    if not is_admin_session_valid(admin, session_id, client_type):
        raise credentials_exception
    return admin


# 兼容现有导入路径
get_current_user_async = get_current_user
get_current_admin_async = get_current_admin
