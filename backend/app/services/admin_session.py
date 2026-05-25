from datetime import datetime
from typing import Optional

from app.models.admin import Admin

ADMIN_DUAL_SESSION_USERNAME = "xiaojiang"
ADMIN_CLIENT_WEB = "WEB"
ADMIN_CLIENT_MOBILE = "MOBILE"


def normalize_admin_client_type(client_type: Optional[str]) -> str:
    """规范化后台登录端类型。

    :param client_type: 前端传入的端类型
    :return: 规范化后的端类型，取值为 WEB 或 MOBILE
    """
    raw_value = str(client_type or "").strip().upper()
    if raw_value in {"MOBILE", "ANDROID", "APP"}:
        return ADMIN_CLIENT_MOBILE
    return ADMIN_CLIENT_WEB


def is_dual_session_admin(admin: Admin) -> bool:
    """判断后台账号是否允许 Web 与移动端同时在线。

    :param admin: 后台管理员对象
    :return: 允许双端在线时返回 True
    """
    return getattr(admin, "username", None) == ADMIN_DUAL_SESSION_USERNAME


def assign_admin_session(admin: Admin, session_id: str, client_type: Optional[str], issued_at: datetime) -> str:
    """写入后台管理员登录会话。

    :param admin: 后台管理员对象
    :param session_id: 本次登录生成的会话 ID
    :param client_type: 登录端类型
    :param issued_at: 会话签发时间
    :return: 规范化后的端类型
    """
    normalized_client_type = normalize_admin_client_type(client_type)
    admin.active_session_id = session_id
    admin.active_session_issued_at = issued_at
    if not is_dual_session_admin(admin):
        return normalized_client_type

    # xiaojiang 是唯一允许双端在线的账号，因此按端类型分别保存会话。
    if normalized_client_type == ADMIN_CLIENT_MOBILE:
        admin.active_mobile_session_id = session_id
        admin.active_mobile_session_issued_at = issued_at
    else:
        admin.active_web_session_id = session_id
        admin.active_web_session_issued_at = issued_at
    return normalized_client_type


def is_admin_session_valid(admin: Admin, session_id: str, client_type: Optional[str]) -> bool:
    """校验后台管理员 token 是否仍为有效会话。

    :param admin: 后台管理员对象
    :param session_id: token 中的会话 ID
    :param client_type: token 中的端类型
    :return: 会话有效时返回 True
    """
    normalized_client_type = normalize_admin_client_type(client_type)
    if not is_dual_session_admin(admin):
        return getattr(admin, "active_session_id", None) == session_id

    expected_session_id = (
        getattr(admin, "active_mobile_session_id", None)
        if normalized_client_type == ADMIN_CLIENT_MOBILE
        else getattr(admin, "active_web_session_id", None)
    )
    if expected_session_id:
        return expected_session_id == session_id
    return getattr(admin, "active_session_id", None) == session_id
