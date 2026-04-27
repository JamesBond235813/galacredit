from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_async_db
from app.models.user import User
from app.models.admin import Admin

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
        if phone is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    if user is None:
        raise credentials_exception
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
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = (await db.execute(select(Admin).where(Admin.username == username))).scalar_one_or_none()
    if admin is None:
        raise credentials_exception
    return admin


# 兼容现有导入路径
get_current_user_async = get_current_user
get_current_admin_async = get_current_admin
