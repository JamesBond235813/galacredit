from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
import bcrypt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _bcrypt_bytes(password: str) -> bytes:
    return str(password or "").encode("utf-8")[:72]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_bcrypt_bytes(plain_password), str(hashed_password or "").encode("utf-8"))
    except Exception:
        return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_bcrypt_bytes(password), bcrypt.gensalt()).decode("utf-8")

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None, jti: str = None, client_id: str = None
) -> str:
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "typ": "access"}
    if jti:
        to_encode["jti"] = jti
    if client_id:
        to_encode["cid"] = client_id
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: timedelta = None, jti: str = None, client_id: str = None
) -> str:
    """创建刷新令牌。

    :param subject: JWT subject，当前使用手机号
    :param expires_delta: 过期时间增量
    :param jti: 刷新令牌唯一ID
    :param client_id: 客户端ID
    :return: 编码后的 refresh token
    """
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "typ": "refresh"}
    if jti:
        to_encode["jti"] = jti
    if client_id:
        to_encode["cid"] = client_id
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
