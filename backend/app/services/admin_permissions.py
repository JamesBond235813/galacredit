import json
from typing import Iterable, List, Optional


ADMIN_PAGE_OPTIONS = [
    {"key": "overview", "label": "洞察看板", "route": "/overview"},
    {"key": "users", "label": "用户档案", "route": "/users"},
    {"key": "applications", "label": "申请审批", "route": "/applications"},
    {"key": "disbursements", "label": "待发卡", "route": "/disbursements"},
    {"key": "repayments", "label": "还款管理", "route": "/repayments"},
    {"key": "collections", "label": "催收管理", "route": "/collections"},
    {"key": "financials", "label": "财务平账", "route": "/financials"},
    {"key": "products", "label": "商品管理", "route": "/products"},
    {"key": "ecard-pool", "label": "卡池管理", "route": "/ecard-pool"},
    {"key": "channels", "label": "渠道管理", "route": "/channels"},
    {"key": "exclusive-links", "label": "专属链接", "route": "/exclusive-links"},
    {"key": "admin-users", "label": "后台用户", "route": "/admin-users"},
]

ALL_ADMIN_PERMISSION_KEYS = [item["key"] for item in ADMIN_PAGE_OPTIONS]

ADMIN_ROLE_OPTIONS = [
    {"key": "ADMIN", "label": "管理员"},
    {"key": "REVIEW", "label": "审核"},
    {"key": "FINANCE", "label": "财务"},
    {"key": "COLLECTION", "label": "催收"},
    {"key": "BUSINESS_CONSULTANT", "label": "业务顾问"},
]

ALL_ADMIN_ROLE_KEYS = [item["key"] for item in ADMIN_ROLE_OPTIONS]

ADMIN_ROLE_PERMISSION_MAP = {
    "ADMIN": list(ALL_ADMIN_PERMISSION_KEYS),
    "REVIEW": ["users", "applications", "repayments"],
    "FINANCE": ["disbursements", "financials", "products", "ecard-pool"],
    "COLLECTION": ["collections"],
    "BUSINESS_CONSULTANT": ["users", "exclusive-links"],
}

ADMIN_ROLE_LABEL_MAP = {item["key"]: item["label"] for item in ADMIN_ROLE_OPTIONS}


def normalize_admin_permissions(values: Optional[Iterable[str]]) -> List[str]:
    if values is None:
        return list(ALL_ADMIN_PERMISSION_KEYS)

    normalized = []
    for item in values:
        key = str(item or "").strip()
        if key in ALL_ADMIN_PERMISSION_KEYS and key not in normalized:
            normalized.append(key)
    return normalized


def normalize_admin_roles(values: Optional[Iterable[str]]) -> List[str]:
    if values is None:
        return []

    normalized = []
    for item in values:
        key = str(item or "").strip().upper()
        if key in ALL_ADMIN_ROLE_KEYS and key not in normalized:
            normalized.append(key)
    return normalized


def serialize_admin_permissions(values: Optional[Iterable[str]]) -> str:
    return json.dumps(normalize_admin_permissions(values), ensure_ascii=False)


def serialize_admin_roles(values: Optional[Iterable[str]]) -> str:
    return json.dumps(normalize_admin_roles(values), ensure_ascii=False)


def parse_admin_permissions(raw_value) -> List[str]:
    if raw_value in (None, ""):
        return list(ALL_ADMIN_PERMISSION_KEYS)

    if isinstance(raw_value, (list, tuple, set)):
        return normalize_admin_permissions(raw_value)

    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        decoded = str(raw_value).split(",")
    return normalize_admin_permissions(decoded)


def parse_admin_roles(raw_value) -> List[str]:
    if raw_value in (None, ""):
        return []

    if isinstance(raw_value, (list, tuple, set)):
        return normalize_admin_roles(raw_value)

    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        decoded = str(raw_value).split(",")
    return normalize_admin_roles(decoded)


def resolve_permissions_from_roles(roles: Optional[Iterable[str]]) -> List[str]:
    normalized_roles = normalize_admin_roles(roles)
    if not normalized_roles:
        return []

    permissions = []
    for role in normalized_roles:
        role_permissions = ADMIN_ROLE_PERMISSION_MAP.get(role, [])
        for item in role_permissions:
            if item in ALL_ADMIN_PERMISSION_KEYS and item not in permissions:
                permissions.append(item)
    return permissions


def resolve_admin_permissions(admin) -> List[str]:
    roles = parse_admin_roles(getattr(admin, "roles", None))
    # 业务顾问账号强制只允许访问用户档案页，避免被显式权限放大。
    if roles == ["BUSINESS_CONSULTANT"]:
        return ["users", "exclusive-links"]
    role_permissions = resolve_permissions_from_roles(roles)

    raw_permissions = getattr(admin, "permissions", None)
    if raw_permissions in (None, "") and roles:
        explicit_permissions = []
    else:
        explicit_permissions = parse_admin_permissions(raw_permissions)
    merged_permissions = []
    for key in [*role_permissions, *explicit_permissions]:
        if key in ALL_ADMIN_PERMISSION_KEYS and key not in merged_permissions:
            merged_permissions.append(key)

    if merged_permissions:
        return merged_permissions
    return list(ALL_ADMIN_PERMISSION_KEYS)


def admin_has_permission(admin, permission_key: Optional[str]) -> bool:
    if not permission_key:
        return True
    return permission_key in resolve_admin_permissions(admin)
