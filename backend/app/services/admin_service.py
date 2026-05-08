import asyncio
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Optional
import string
import secrets

import xlrd
from fastapi import Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_admin_by_token_async, get_current_admin_async
from app.core.config import settings
from app.core.database import get_async_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.trace import new_trace_id, reset_trace_id, set_trace_id
from app.models.admin import Admin
from app.models.channel import Channel
from app.models.ecard_pool import EcardPool
from app.models.loan import Loan
from app.models.loan_transaction import LoanTransaction
from app.models.product import Product
from app.models.user import User
from app.models.user_event import UserEvent
from app.schemas.admin import (
    AdminLogin,
    AdminTokenResponse,
    RegisterUserRequest,
    ResetUserPasswordRequest,
    AdminResponse,
    AdminUserCreateRequest,
    AdminUserItemResponse,
    AdminUserUpdateRequest,
    PaginatedAdminUserResponse,
    AdminChangePasswordRequest,
)
from app.schemas.channel import (
    BusinessAdvisorItemResponse,
    ChannelCreateRequest,
    ChannelUpdateRequest,
    PaginatedChannelResponse,
)
from app.schemas.loan import (
    AdminStatsResponse,
    DisburseRequest,
    EcardPoolCreateRequest,
    EcardPoolUpdateRequest,
    LoanAssigneeItemResponse,
    LoanAssignmentResponse,
    LoanAssignRequest,
    LoanLedgerResponse,
    LoanFinanceReconcileRequest,
    LoanFollowUpRequest,
    ProjectCashInsightResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    RepayAttemptAckResponse,
    RepaymentStatsResponse,
    LoanReviewRequest,
    LoanUpdateRequest,
    PaginatedEcardPoolResponse,
    PaginatedProductResponse,
    PaginatedLoanResponse,
)
from app.schemas.risk import AdminRiskReportRequest, RiskReportResponse
from app.schemas.user import PaginatedUserResponse, UserDetailResponse
from app.services.audit import log_user_event_async
from app.services.admin_permissions import (
    ALL_ADMIN_PERMISSION_KEYS,
    admin_has_permission,
    parse_admin_roles,
    parse_admin_permissions,
    resolve_admin_permissions,
    resolve_permissions_from_roles,
    serialize_admin_permissions,
    serialize_admin_roles,
)
from app.services.channel_service import (
    build_channel_metrics,
    build_channel_summary,
    get_channel_by_name_async,
    normalize_channel_name,
    normalize_channel_status,
    serialize_channel_landing,
)
from app.services.loan_amounts import (
    DEFAULT_FEE_RATE,
    calculate_remaining_repayment_amount,
    calculate_total_repayment_amount,
    normalize_fee_rate,
    normalize_term_days,
    serialize_loan_snapshot,
    sync_loan_fee_fields,
)
from app.services.loan_ledger import (
    create_disbursement_transaction_async,
    ensure_installment_records_async,
    get_loan_ledger_snapshot,
    register_reduction_async,
    register_repayment_async,
    serialize_transaction,
    sync_loan_repayment_state,
)
from app.services.loan_flow import (
    get_latest_loan_async,
    get_latest_normal_settled_loan,
    get_relend_count,
    get_relend_label,
)
from app.services.loan_assignment import (
    COLLECTION_TRANSFER_OVERDUE_DAYS,
    admin_has_role,
    assign_collection_admin_if_needed_async,
    assign_collection_admins_for_overdue_loans_async,
    assign_review_admin_if_needed_async,
    is_collection_stage,
    list_admins_by_role_async,
)
from app.services.risk_report import (
    get_or_create_risk_report_async,
    get_user_for_risk_report_async,
    serialize_risk_report,
)


LOAN_STATUSES = {
    "INIT",
    "REVIEWING",
    "APPROVED",
    "REJECTED",
    "WITHDRAWING",
    "DISBURSED",
    "SETTLED",
    "OVERDUE",
}

LOAN_PAGE_PERMISSION_KEYS = (
    "applications",
    "disbursements",
    "repayments",
    "collections",
    "financials",
)

ADMIN_STATS_PERMISSION_KEYS = (
    "overview",
    "applications",
    "disbursements",
    "repayments",
    "collections",
    "financials",
)

REPAYMENT_STATS_PERMISSION_KEYS = (
    "overview",
    "repayments",
    "financials",
)

ECARD_POOL_STATUSES = {"AVAILABLE", "ASSIGNED", "EXPIRED", "VOID"}
ADMIN_STATS_WS_PUSH_SECONDS = 5

_ADMIN_STATS_VERSION = 0


async def notify_admin_stats_changed():
    """标记后台统计数据已变化，并唤醒等待中的 WS 推送循环。

    :return: None
    """
    global _ADMIN_STATS_VERSION
    _ADMIN_STATS_VERSION += 1


async def wait_admin_stats_changed(last_version: int, timeout_seconds: float):
    """等待后台统计数据变更；超时则返回当前版本用于兜底推送。

    :param last_version: 上次已推送版本
    :param timeout_seconds: 超时时间（秒）
    :return: 最新版本号
    """
    if _ADMIN_STATS_VERSION != last_version:
        return _ADMIN_STATS_VERSION

    deadline = asyncio.get_running_loop().time() + max(float(timeout_seconds or 0), 0)
    while asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.5)
        if _ADMIN_STATS_VERSION != last_version:
            return _ADMIN_STATS_VERSION
    return _ADMIN_STATS_VERSION



def get_today_range():
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    tomorrow = today_start + timedelta(days=1)
    return today_start, tomorrow

async def _get_ws_admin_by_token(db: AsyncSession, token: Optional[str]) -> Optional[Admin]:
    """通过 WebSocket Token 获取管理员。

    :param db: 异步数据库会话
    :param token: token 字符串
    :return: 管理员对象；token 非法或为空时返回 None
    """
    if not token:
        return None
    try:
        return await get_admin_by_token_async(db, token)
    except HTTPException:
        return None

def _extract_ws_token(websocket: WebSocket) -> Optional[str]:
    """提取 WebSocket 连接中的管理员 token。

    :param websocket: WebSocket 连接对象
    :return: token 字符串
    """
    query_token = websocket.query_params.get("token")
    if query_token:
        return query_token
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip() or None
    return None

def calculate_due_date(disbursed_at: datetime, term_days: Optional[int]):
    if not disbursed_at or not term_days:
        return None

    offset_days = max(int(term_days) - 1, 0)
    return disbursed_at + timedelta(days=offset_days)

def ensure_valid_term_days(term_days: Optional[int]) -> Optional[int]:
    if term_days is None:
        return None

    try:
        return normalize_term_days(term_days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

def serialize_admin_user(admin: Admin, current_admin: Optional[Admin] = None):
    roles = parse_admin_roles(getattr(admin, "roles", None))
    return {
        "id": admin.id,
        "username": admin.username,
        "roles": roles,
        "permissions": resolve_admin_permissions(admin),
        "created_at": admin.created_at,
        "updated_at": admin.updated_at,
        "is_current": bool(current_admin and admin.id == current_admin.id),
    }

def resolve_roles_and_permissions(roles_input, permissions_input):
    roles = parse_admin_roles(roles_input)
    if roles:
        return roles, resolve_permissions_from_roles(roles)

    permissions = [
        item for item in parse_admin_permissions(permissions_input)
        if item in ALL_ADMIN_PERMISSION_KEYS
    ]
    if permissions:
        # 兼容旧请求：仅传页面权限时，按页面权限落库
        return [], permissions
    return [], []

def ensure_admin_page_permission(current_admin: Admin, permission_key: str):
    if not admin_has_permission(current_admin, permission_key):
        raise HTTPException(status_code=403, detail="无权访问当前页面")

def ensure_any_admin_page_permission(current_admin: Admin, permission_keys):
    if any(admin_has_permission(current_admin, item) for item in permission_keys):
        return
    raise HTTPException(status_code=403, detail="无权访问当前页面")

def resolve_loan_scope_permission(
    scope: Optional[str],
    due_date_preset: Optional[str],
    status: Optional[str] = None,
):
    if scope == "REVIEWING":
        return "applications"
    if scope == "WITHDRAWING":
        return "disbursements"
    if scope == "FINANCE":
        return "financials"
    if scope == "OVERDUE":
        return "collections"
    if scope == "DUE_TODAY" or due_date_preset in {"TODAY", "TOMORROW"}:
        return "repayments"
    if scope == "REPAYMENTS":
        return "repayments"

    if status in {"REVIEWING", "APPROVED", "REJECTED"}:
        return "applications"
    if status == "WITHDRAWING":
        return "disbursements"
    if status in {"DISBURSED", "SETTLED"}:
        return "repayments"
    if status == "OVERDUE":
        return "collections"

    return None

def current_admin_roles(current_admin: Admin):
    return parse_admin_roles(getattr(current_admin, "roles", None))

def is_super_admin(current_admin: Admin) -> bool:
    return "ADMIN" in current_admin_roles(current_admin)

def ensure_stage_access_for_admin(current_admin: Admin, loan: Loan):
    roles = current_admin_roles(current_admin)
    if "ADMIN" in roles:
        return
    if is_collection_stage(loan):
        if "COLLECTION" in roles and int(loan.collection_admin_id or 0) == int(current_admin.id):
            return
        raise HTTPException(status_code=403, detail="当前订单已转催收，仅限负责催收员处理")

    if "REVIEW" in roles and int(loan.review_admin_id or 0) == int(current_admin.id):
        return
    if "FINANCE" in roles and loan.status in {"DISBURSED", "OVERDUE", "SETTLED", "WITHDRAWING"}:
        return

    raise HTTPException(status_code=403, detail="当前订单未分配给你处理")

def serialize_loan(loan: Loan):
    owner_loans = getattr(getattr(loan, "owner", None), "loans", None) or []
    loan.relend_count = get_relend_count(owner_loans, current_loan_id=loan.id)
    loan.relend_label = get_relend_label(owner_loans, current_loan_id=loan.id)
    loan.latest_settled_loan = get_latest_normal_settled_loan(owner_loans, current_loan_id=loan.id)
    payload = serialize_loan_snapshot(loan, include_user=True)
    payload["review_admin_id"] = loan.review_admin_id
    payload["review_admin_name"] = None
    payload["collection_admin_id"] = loan.collection_admin_id
    payload["collection_admin_name"] = None
    payload["collection_transferred_at"] = loan.collection_transferred_at

    if loan.review_admin_id:
        reviewer = getattr(loan, "review_admin", None)
        payload["review_admin_name"] = reviewer.username if reviewer else None
    if loan.collection_admin_id:
        collector = getattr(loan, "collection_admin", None)
        payload["collection_admin_name"] = collector.username if collector else None
    return payload

def serialize_user_summary(user: User):
    latest_loan = max(user.loans, key=lambda item: item.id) if user.loans else None
    if latest_loan:
        latest_loan.relend_count = get_relend_count(user.loans, current_loan_id=latest_loan.id)
        latest_loan.relend_label = get_relend_label(user.loans, current_loan_id=latest_loan.id)
        latest_loan.latest_settled_loan = get_latest_normal_settled_loan(user.loans, current_loan_id=latest_loan.id)
    loan_snapshot = serialize_loan_snapshot(latest_loan) if latest_loan else None
    disbursed_loans = [item for item in (user.loans or []) if getattr(item, "disbursed_at", None)]
    first_deal_loan = min(disbursed_loans, key=lambda item: item.id) if disbursed_loans else None
    latest_deal_loan = max(disbursed_loans, key=lambda item: item.id) if disbursed_loans else None
    source_channel = user.source_channel
    return {
        "id": user.id,
        "phone": mask_secret(user.phone, left=0, right=4),
        "name": user.name,
        "id_card_num": mask_secret(user.id_card_num, left=6, right=1),
        "face_auth_status": user.face_auth_status,
        "approved_limit": user.approved_limit,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "application_submitted_at": user.application_submitted_at,
        "current_loan_id": latest_loan.id if latest_loan else None,
        "current_loan_status": latest_loan.status if latest_loan else None,
        "current_credit_limit": loan_snapshot["credit_limit"] if loan_snapshot else None,
        "current_term_days": loan_snapshot["term_days"] if loan_snapshot else None,
        "current_due_date": loan_snapshot["due_date"] if loan_snapshot else None,
        "current_fee_rate": loan_snapshot["fee_rate"] if loan_snapshot else None,
        "current_fee_amount": loan_snapshot["fee_amount"] if loan_snapshot else None,
        "current_interest_amount": loan_snapshot["interest_amount"] if loan_snapshot else None,
        "current_guarantee_fee_amount": loan_snapshot["guarantee_fee_amount"] if loan_snapshot else None,
        "current_penalty_amount": loan_snapshot["penalty_amount"] if loan_snapshot else None,
        "first_disbursed_at": getattr(first_deal_loan, "disbursed_at", None),
        "first_deal_amount": round_money(getattr(first_deal_loan, "product_total_price", 0)) if first_deal_loan else None,
        "latest_disbursed_at": getattr(latest_deal_loan, "disbursed_at", None),
        "latest_deal_amount": round_money(getattr(latest_deal_loan, "product_total_price", 0)) if latest_deal_loan else None,
        "source_channel_name": source_channel.channel_name if source_channel else None,
        "source_channel_sales_name": source_channel.sales_name if source_channel else None,
        "channel_bound_at": user.channel_bound_at,
        "last_channel_visit_at": user.last_channel_visit_at,
    }

def serialize_user_detail(user: User, events: Optional[list[UserEvent]] = None):
    latest_loan = max(user.loans, key=lambda item: item.id) if user.loans else None
    if latest_loan:
        latest_loan.relend_count = get_relend_count(user.loans, current_loan_id=latest_loan.id)
        latest_loan.relend_label = get_relend_label(user.loans, current_loan_id=latest_loan.id)
        latest_loan.latest_settled_loan = get_latest_normal_settled_loan(user.loans, current_loan_id=latest_loan.id)
    event_list = sorted(events or [], key=lambda item: item.created_at, reverse=True)
    source_channel = user.source_channel
    # 首次成交口径：优先第一条非拒绝订单，取不到时回退第一条订单。
    sorted_loans = sorted(user.loans or [], key=lambda item: (item.created_at or datetime.min, item.id or 0))
    first_deal_loan = next((item for item in sorted_loans if item.status != "REJECTED"), None)
    if first_deal_loan is None and sorted_loans:
        first_deal_loan = sorted_loans[0]
    if first_deal_loan:
        first_deal_loan.relend_count = get_relend_count(user.loans, current_loan_id=first_deal_loan.id)
        first_deal_loan.relend_label = get_relend_label(user.loans, current_loan_id=first_deal_loan.id)
        first_deal_loan.latest_settled_loan = get_latest_normal_settled_loan(user.loans, current_loan_id=first_deal_loan.id)
    return {
        "id": user.id,
        "phone": user.phone,
        "name": user.name,
        "id_card_num": user.id_card_num,
        "id_address": user.id_address,
        "id_expiry": user.id_expiry,
        "approved_limit": user.approved_limit,
        "emergency_contact1_name": user.emergency_contact1_name,
        "emergency_contact1_relation": user.emergency_contact1_relation,
        "emergency_contact1_phone": user.emergency_contact1_phone,
        "emergency_contact2_name": user.emergency_contact2_name,
        "emergency_contact2_relation": user.emergency_contact2_relation,
        "emergency_contact2_phone": user.emergency_contact2_phone,
        "location_latitude": user.location_latitude,
        "location_longitude": user.location_longitude,
        "location_accuracy": user.location_accuracy,
        "location_address": user.location_address,
        "location_province": user.location_province,
        "location_city": user.location_city,
        "location_district": user.location_district,
        "location_street": user.location_street,
        "location_source": user.location_source,
        "location_updated_at": user.location_updated_at,
        "face_auth_status": user.face_auth_status,
        "face_auth_at": user.face_auth_at,
        "last_login_at": user.last_login_at,
        "ocr_submitted_at": user.ocr_submitted_at,
        "application_submitted_at": user.application_submitted_at,
        "source_channel_name": source_channel.channel_name if source_channel else None,
        "source_channel_sales_name": source_channel.sales_name if source_channel else None,
        "channel_bound_at": user.channel_bound_at,
        "last_channel_visit_at": user.last_channel_visit_at,
        "created_at": user.created_at,
        "latest_loan": serialize_loan_snapshot(latest_loan, include_ledger=True) if latest_loan else None,
        "first_deal_loan": serialize_loan_snapshot(first_deal_loan, include_ledger=True) if first_deal_loan else None,
        "events": [
            {
                "id": event.id,
                "loan_id": event.loan_id,
                "actor_type": event.actor_type,
                "operator_name": event.operator_name,
                "event_type": event.event_type,
                "title": event.title,
                "detail": event.detail,
                "created_at": event.created_at,
            }
            for event in event_list
        ],
    }

def serialize_channel(channel: Channel, advisor: Optional[Admin] = None):
    payload = build_channel_metrics(channel)
    payload["invite_code"] = channel.invite_code
    payload["admin_user_id"] = channel.admin_user_id
    payload["admin_user_name"] = advisor.username if advisor else None
    return payload

def _generate_channel_invite_code(length: int = 16) -> str:
    """生成渠道邀请码。

    :param length: 邀请码长度
    :return: 邀请码
    """
    alphabet = string.ascii_lowercase + string.digits
    while True:
        invite_code = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(char.isalpha() for char in invite_code) and any(char.isdigit() for char in invite_code):
            return invite_code


async def _generate_unique_channel_invite_code(db: AsyncSession, length: int = 16) -> str:
    """生成数据库内唯一的渠道邀请码。

    :param db: 异步数据库会话
    :param length: 邀请码长度
    :return: 唯一邀请码
    """
    for _ in range(10):
        invite_code = _generate_channel_invite_code(length)
        exists = (await db.execute(select(Channel).where(Channel.invite_code == invite_code))).scalar_one_or_none()
        if not exists:
            return invite_code
    raise HTTPException(status_code=500, detail="生成渠道邀请码失败，请稍后重试")


def _is_business_consultant(admin: Optional[Admin]) -> bool:
    """判断后台用户是否为业务顾问角色（严格匹配，不包含 ADMIN 兜底）。

    :param admin: 后台用户对象
    :return: 是否包含 BUSINESS_CONSULTANT 角色
    """
    if admin is None:
        return False
    return "BUSINESS_CONSULTANT" in parse_admin_roles(getattr(admin, "roles", None))

def _is_only_business_consultant(admin: Optional[Admin]) -> bool:
    """判断后台用户是否为仅业务顾问角色。

    :param admin: 后台用户对象
    :return: 是否有且仅有 BUSINESS_CONSULTANT 角色
    """
    if admin is None:
        return False
    roles = parse_admin_roles(getattr(admin, "roles", None))
    return len(roles) == 1 and roles[0] == "BUSINESS_CONSULTANT"

def apply_business_consultant_user_summary_status(user_summary: dict, admin: Optional[Admin]) -> dict:
    """按业务顾问规则调整用户列表状态展示值。

    :param user_summary: 用户列表摘要数据
    :param admin: 当前登录后台用户
    :return: 调整后的用户列表摘要数据
    """
    if _is_only_business_consultant(admin) and user_summary.get("first_disbursed_at"):
        payload = dict(user_summary)
        payload["current_loan_status"] = "FIRST_BORROW"
        return payload
    return user_summary


async def _resolve_business_advisor_by_id(db: AsyncSession, admin_user_id: int):
    advisor = (await db.execute(select(Admin).where(Admin.id == admin_user_id))).scalar_one_or_none()
    if not _is_business_consultant(advisor):
        raise HTTPException(status_code=400, detail="请选择角色为业务顾问的后台用户")
    return advisor

def round_money(value: Optional[float]) -> float:
    return round(float(value or 0), 2)

def mask_secret(value: Optional[str], left: int = 3, right: int = 2) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) <= left + right:
        return "*" * len(text)
    return f"{text[:left]}{'*' * (len(text) - left - right)}{text[-right:]}"

def resolve_product_payment_amount(ecard_face_value: float, rights_price: float, payment_amount: Optional[float] = None):
    if payment_amount is not None and float(payment_amount) > 0:
        return round_money(payment_amount)
    return round_money(float(ecard_face_value or 0) + float(rights_price or 0))

def serialize_product(product: Product):
    return {
        "id": product.id,
        "name": product.name,
        "ecard_face_value": round_money(product.ecard_face_value),
        "rights_price": round_money(product.rights_price),
        "rights_title": product.rights_title,
        "rights_desc": product.rights_desc,
        "term_days": product.term_days,
        "payment_amount": round_money(product.payment_amount),
        "is_active": bool(product.is_active),
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }

def serialize_ecard_pool_item(item: EcardPool):
    return {
        "id": item.id,
        "account": mask_secret(item.account, left=4, right=4),
        "password": mask_secret(item.password, left=1, right=1),
        "face_value": round_money(item.face_value),
        "expires_at": item.expires_at,
        "status": item.status,
        "loan_id": item.loan_id,
        "note": item.note,
        "assigned_at": item.assigned_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }

def apply_loan_scope(query, scope: Optional[str]):
    overdue_days_expr = func.datediff(func.current_date(), func.date(Loan.due_date))
    today_start, tomorrow = get_today_range()

    if scope == "REVIEWING":
        return query.filter(Loan.status.in_(["REVIEWING", "APPROVED", "REJECTED"]))
    if scope == "WITHDRAWING":
        return query.filter(Loan.status == "WITHDRAWING")
    if scope == "FINANCE":
        return query.filter(Loan.status.in_(["DISBURSED", "OVERDUE"]))
    if scope == "DUE_TODAY":
        return query.filter(
            Loan.status.in_(["DISBURSED", "OVERDUE"]),
            Loan.due_date >= today_start,
            Loan.due_date < tomorrow,
        )
    if scope == "OVERDUE":
        return query.filter(
            Loan.status == "OVERDUE",
            Loan.due_date.isnot(None),
            overdue_days_expr > COLLECTION_TRANSFER_OVERDUE_DAYS,
        )
    if scope == "REPAYMENTS":
        return query.filter(
            or_(
                Loan.status.in_(["DISBURSED", "SETTLED"]),
                (
                    (Loan.status == "OVERDUE")
                    & Loan.due_date.isnot(None)
                    & (overdue_days_expr <= COLLECTION_TRANSFER_OVERDUE_DAYS)
                ),
            )
        )
    return query

def build_loan_scope_filters(scope: Optional[str]):
    overdue_days_expr = func.datediff(func.current_date(), func.date(Loan.due_date))
    today_start, tomorrow = get_today_range()

    if scope == "REVIEWING":
        return [Loan.status.in_(["REVIEWING", "APPROVED", "REJECTED"])]
    if scope == "WITHDRAWING":
        return [Loan.status == "WITHDRAWING"]
    if scope == "FINANCE":
        return [Loan.status.in_(["DISBURSED", "OVERDUE"])]
    if scope == "DUE_TODAY":
        return [
            Loan.status.in_(["DISBURSED", "OVERDUE"]),
            Loan.due_date >= today_start,
            Loan.due_date < tomorrow,
        ]
    if scope == "OVERDUE":
        return [
            Loan.status == "OVERDUE",
            Loan.due_date.isnot(None),
            overdue_days_expr > COLLECTION_TRANSFER_OVERDUE_DAYS,
        ]
    if scope == "REPAYMENTS":
        return [
            or_(
                Loan.status.in_(["DISBURSED", "SETTLED"]),
                (
                    (Loan.status == "OVERDUE")
                    & Loan.due_date.isnot(None)
                    & (overdue_days_expr <= COLLECTION_TRANSFER_OVERDUE_DAYS)
                ),
            )
        ]
    return []

def get_overdue_days_expr():
    return func.greatest(func.datediff(func.current_date(), func.date(Loan.due_date)), 1)

def get_loan_operating_metrics(loan: Loan):
    ledger = get_loan_ledger_snapshot(loan)
    return ledger["summary"]

def round_cash_amount(value: Optional[float]) -> float:
    return round(float(value or 0), 2)

async def build_project_cash_insights(db: AsyncSession, loans, today_start: datetime, tomorrow: datetime):
    ordered_statuses = {"WITHDRAWING", "DISBURSED", "OVERDUE", "SETTLED"}
    issued_statuses = {"DISBURSED", "OVERDUE", "SETTLED"}

    order_loans = [loan for loan in loans if loan.status in ordered_statuses and float(loan.credit_limit or loan.ecard_face_value or 0) > 0]
    issued_loans = [loan for loan in order_loans if loan.status in issued_statuses]
    overdue_loans = [loan for loan in issued_loans if loan.status == "OVERDUE"]
    normal_outstanding_loans = [loan for loan in issued_loans if loan.status == "DISBURSED"]

    total_users = (await db.scalar(select(func.count(User.id)))) or 0
    today_new_users = (
        await db.scalar(
            select(func.count(User.id)).where(User.created_at >= today_start, User.created_at < tomorrow)
        )
    ) or 0

    today_order_count = (
        await db.scalar(
            select(func.count(func.distinct(UserEvent.loan_id))).where(
                UserEvent.event_type == "ORDER_SUBMIT",
                UserEvent.loan_id.isnot(None),
                UserEvent.created_at >= today_start,
                UserEvent.created_at < tomorrow,
            )
        )
    ) or 0

    today_received_amount = (
        await db.scalar(
            select(func.coalesce(func.sum(LoanTransaction.amount), 0)).where(
                LoanTransaction.transaction_type.in_(["REPAYMENT", "SETTLEMENT"]),
                LoanTransaction.created_at >= today_start,
                LoanTransaction.created_at < tomorrow,
            )
        )
    ) or 0

    today_issued_loans = [
        loan
        for loan in issued_loans
        if loan.disbursed_at and today_start <= loan.disbursed_at < tomorrow
    ]

    total_ecard_issued = round_cash_amount(sum(float(loan.ecard_face_value or loan.credit_limit or 0) for loan in issued_loans))
    today_ecard_issued = round_cash_amount(
        sum(float(loan.ecard_face_value or loan.credit_limit or 0) for loan in today_issued_loans)
    )

    total_rights_cost = round_cash_amount(sum(float(loan.rights_price or 0) * 0.04 for loan in issued_loans))
    today_rights_cost = round_cash_amount(sum(float(loan.rights_price or 0) * 0.04 for loan in today_issued_loans))

    order_total_amount = round_cash_amount(sum(calculate_total_repayment_amount(loan) for loan in issued_loans))
    today_order_total_amount = round_cash_amount(sum(calculate_total_repayment_amount(loan) for loan in today_issued_loans))

    receivable_amount = round_cash_amount(sum(calculate_remaining_repayment_amount(loan) for loan in issued_loans))
    today_new_receivable_amount = round_cash_amount(sum(calculate_total_repayment_amount(loan) for loan in today_issued_loans))

    overdue_outstanding_amount = round_cash_amount(sum(calculate_remaining_repayment_amount(loan) for loan in overdue_loans))
    yesterday_overdue_outstanding_amount = round_cash_amount(
        sum(
            calculate_remaining_repayment_amount(loan)
            for loan in overdue_loans
            if loan.due_date and loan.due_date < today_start
        )
    )

    pending_normal_outstanding_amount = round_cash_amount(
        sum(calculate_remaining_repayment_amount(loan) for loan in normal_outstanding_loans)
    )

    cards = [
        {
            "key": "registered_users",
            "title": "注册数",
            "value": int(total_users),
            "value_type": "count",
            "sub_label": "今日注册数",
            "sub_value": int(today_new_users),
        },
        {
            "key": "order_count",
            "title": "下单数",
            "value": int(len(order_loans)),
            "value_type": "count",
            "sub_label": "今日下单数",
            "sub_value": int(today_order_count),
        },
        {
            "key": "ecard_issued_amount",
            "title": "E卡发放总额",
            "value": total_ecard_issued,
            "value_type": "currency",
            "sub_label": "今日E卡发放总额",
            "sub_value": today_ecard_issued,
        },
        {
            "key": "rights_cost",
            "title": "权益成本",
            "value": total_rights_cost,
            "value_type": "currency",
            "sub_label": "今日权益成本",
            "sub_value": today_rights_cost,
        },
        {
            "key": "overdue_amount",
            "title": "累计逾期",
            "value": overdue_outstanding_amount,
            "value_type": "currency",
            "sub_label": "昨日累计逾期金额",
            "sub_value": yesterday_overdue_outstanding_amount,
        },
        {
            "key": "issued_order_count",
            "title": "放款单数",
            "value": int(len(issued_loans)),
            "value_type": "count",
            "sub_label": "今日放款单数",
            "sub_value": int(len(today_issued_loans)),
        },
        {
            "key": "order_total_amount",
            "title": "订单总额",
            "value": order_total_amount,
            "value_type": "currency",
            "sub_label": "今日订单总额",
            "sub_value": today_order_total_amount,
        },
        {
            "key": "received_amount",
            "title": "收款金额",
            "value": round_cash_amount(sum(float(loan.repaid_amount or 0) for loan in issued_loans)),
            "value_type": "currency",
            "sub_label": "今日收款金额",
            "sub_value": round_cash_amount(today_received_amount),
        },
        {
            "key": "receivable_amount",
            "title": "应收金额",
            "value": receivable_amount,
            "value_type": "currency",
            "sub_label": "今日新增应收金额",
            "sub_value": today_new_receivable_amount,
        },
        {
            "key": "pending_non_overdue_amount",
            "title": "待回收未逾期总资金",
            "value": pending_normal_outstanding_amount,
            "value_type": "currency",
            "sub_label": "--",
            "sub_value": 0,
        },
    ]

    return {
        "total_projects": 0,
        "total_borrowers": int(len({loan.user_id for loan in issued_loans})),
        "total_loans": int(len(issued_loans)),
        "total_payment_amount": 0,
        "total_receipt_amount": round_cash_amount(sum(float(loan.repaid_amount or 0) for loan in issued_loans)),
        "total_net_amount": round_cash_amount(
            sum(float(loan.repaid_amount or 0) for loan in issued_loans) - total_ecard_issued - total_rights_cost
        ),
        "notes": [
            "利息、融担费等科目的“付款”口径为减免/退费金额，不是用户额外打款。",
            "权益成本按每份已发出权益的权益定价 × 4% 计算。",
            "应收金额为截至当前未回收的应收总额（剩余待还）。",
        ],
        "cards": cards,
        "items": [],
    }

async def _register_user(
    db: AsyncSession,
    current_admin: Admin,
    req: RegisterUserRequest,
):
    """后台新增前端用户。

    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :param req: 新增用户请求体
    :return: 新增结果
    """
    ensure_admin_page_permission(current_admin, "users")
    channel = None
    if req.source_channel_id is not None:
        channel = (
            await db.execute(
                select(Channel).where(
                    Channel.id == req.source_channel_id,
                    Channel.status == "ACTIVE",
                )
            )
        ).scalar_one_or_none()
        if channel is None:
            raise HTTPException(status_code=400, detail="来源渠道不存在或未启用")

    existed = (await db.execute(select(User).where(User.phone == req.phone))).scalar_one_or_none()
    if existed is not None:
        raise HTTPException(status_code=400, detail="手机号已存在")

    now = datetime.now()
    user = User(
        phone=req.phone,
        password_hash=get_password_hash(req.password),
        face_auth_status="PENDING",
        source_channel_id=channel.id if channel else None,
        channel_bound_at=now if channel else None,
        last_channel_visit_at=now if channel else None,
    )
    db.add(user)
    await db.flush()

    # 审计记录用于追踪管理员新增用户来源，避免后续归因排查困难。
    await log_user_event_async(
        db,
        user=user,
        loan=None,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_REGISTER_USER",
        title="后台新增用户",
        detail=(
            f"后台新增用户，来源渠道：{channel.sales_name}（{channel.channel_name}）。"
            if channel
            else "后台新增用户，来源渠道：未指定。"
        ),
    )
    await db.commit()
    return {
        "msg": "新增用户成功",
        "user_id": user.id,
        "phone": user.phone,
    }

async def _reset_user_password(
    db: AsyncSession,
    current_admin: Admin,
    user_id: int,
    req: ResetUserPasswordRequest,
):
    """后台重置指定用户密码。

    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :param user_id: 用户ID
    :param req: 重置密码请求体
    :return: 重置结果
    """
    ensure_admin_page_permission(current_admin, "users")
    if _is_business_consultant(current_admin):
        raise HTTPException(status_code=403, detail="业务顾问无权重置密码")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.password_hash = get_password_hash(req.password)
    # 后台重置密码后立即解除该手机号冻结，避免用户已改密但仍被历史失败次数阻断。
    from app.api.endpoints import auth as auth_endpoints
    await auth_endpoints.password_login_guard.on_success(user.phone)
    await log_user_event_async(
        db,
        user=user,
        loan=None,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_RESET_PASSWORD",
        title="后台重置密码",
        detail="管理员已重置用户登录密码。",
    )
    await db.commit()
    return {"msg": "重置密码成功"}


async def _change_admin_password(
    db: AsyncSession,
    current_admin: Admin,
    req: AdminChangePasswordRequest,
):
    """当前登录后台用户修改自身密码。

    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :param req: 修改密码请求体
    :return: 修改结果
    """
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")
    if not verify_password(req.old_password, current_admin.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if req.old_password == req.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码一致")

    current_admin.password_hash = get_password_hash(req.new_password)
    await db.commit()
    return {"msg": "修改密码成功"}

async def _get_loan_ledger(db: AsyncSession, current_admin: Admin, loan_id: int):
    loan = (
        await db.execute(
            select(Loan)
            .options(
                joinedload(Loan.installments),
                joinedload(Loan.transactions),
                joinedload(Loan.review_admin),
                joinedload(Loan.collection_admin),
            )
            .where(Loan.id == loan_id)
        )
    ).unique().scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")

    if loan.status == "OVERDUE":
        ensure_any_admin_page_permission(current_admin, ("repayments", "collections"))
    else:
        permission_key = resolve_loan_scope_permission(None, None, loan.status)
        if permission_key:
            ensure_admin_page_permission(current_admin, permission_key)
        else:
            ensure_any_admin_page_permission(current_admin, LOAN_PAGE_PERMISSION_KEYS)
    ensure_stage_access_for_admin(current_admin, loan)

    ledger = get_loan_ledger_snapshot(loan)
    return {
        "loan_id": loan.id,
        "loan_status": loan.status,
        "installments": ledger["installments"],
        "transactions": [serialize_transaction(item) for item in loan.transactions],
        "fund_flow_summary": ledger["summary"],
    }

async def _get_user_detail(db: AsyncSession, current_admin: Admin, user_id: int):
    ensure_admin_page_permission(current_admin, "users")
    user = (
        await db.execute(
            select(User)
            .options(
                joinedload(User.loans),
                joinedload(User.source_channel),
            )
            .where(User.id == user_id)
        )
    ).unique().scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if _is_business_consultant(current_admin):
        bound_channel = getattr(user, "source_channel", None)
        if not bound_channel or int(bound_channel.admin_user_id or 0) != int(current_admin.id):
            raise HTTPException(status_code=403, detail="无权查看该用户档案")
    events = (
        await db.execute(
            select(UserEvent)
            .where(UserEvent.user_id == user.id)
            .order_by(UserEvent.created_at.desc())
        )
    ).scalars().all()
    return serialize_user_detail(user, events=events)

async def _get_risk_report(db: AsyncSession, req: AdminRiskReportRequest, current_admin: Admin):
    ensure_admin_page_permission(current_admin, "applications")
    user = await get_user_for_risk_report_async(db, req.user_id)
    report = await get_or_create_risk_report_async(
        db,
        name=user.name,
        id_card=user.id_card_num,
        phone=user.phone,
    )
    await log_user_event_async(
        db,
        user=user,
        loan=await get_latest_loan_async(db, user.id),
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_RISK_REPORT",
        title="查询风控报告",
        detail="后台发起全景雷达风控报告查询",
    )
    await db.commit()
    await db.refresh(report)
    return serialize_risk_report(report)

async def _get_channels(db: AsyncSession, current_admin: Admin, keyword: Optional[str], status: Optional[str], skip: int, limit: int):
    ensure_admin_page_permission(current_admin, "channels")
    limit = min(max(limit, 1), 100)
    stmt = select(Channel).options(joinedload(Channel.users).joinedload(User.loans))
    if keyword:
        pattern = f"%{keyword.strip().lower()}%"
        stmt = stmt.where(
            or_(
                Channel.channel_name.like(pattern),
                Channel.sales_name.like(f"%{keyword.strip()}%"),
            )
        )
    if status and status != "ALL":
        stmt = stmt.where(Channel.status == normalize_channel_status(status))
    matched_channels = (await db.execute(stmt.order_by(Channel.created_at.desc()))).unique().scalars().all()
    advisor_ids = {int(item.admin_user_id) for item in matched_channels if item.admin_user_id}
    advisor_map = {}
    if advisor_ids:
        advisors = (await db.execute(select(Admin).where(Admin.id.in_(advisor_ids)))).scalars().all()
        advisor_map = {int(item.id): item for item in advisors}
    channel_items = [serialize_channel(channel, advisor_map.get(int(channel.admin_user_id or 0))) for channel in matched_channels]
    return {
        "total": len(channel_items),
        "page": skip // limit + 1,
        "size": limit,
        "channel_link_prefix": settings.CHANNEL_LINK_PREFIX,
        "summary": build_channel_summary(channel_items),
        "items": channel_items[skip : skip + limit],
    }


async def _get_exclusive_links(db: AsyncSession, current_admin: Admin):
    """获取当前业务顾问可见的专属链接列表。

    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :return: 专属链接列表（最多 50 条，启用中优先）
    """
    ensure_admin_page_permission(current_admin, "exclusive-links")
    stmt = (
        select(Channel)
        .options(joinedload(Channel.users).joinedload(User.loans))
        .where(Channel.admin_user_id == current_admin.id)
        .order_by(
            case((Channel.status == "ACTIVE", 0), else_=1),
            Channel.created_at.desc(),
        )
        .limit(50)
    )
    channels = (await db.execute(stmt)).unique().scalars().all()
    channel_items = [serialize_channel(channel, current_admin) for channel in channels]
    return {
        "channel_link_prefix": settings.CHANNEL_LINK_PREFIX,
        "items": channel_items,
    }


async def _get_user_source_channels(db: AsyncSession, current_admin: Admin, keyword: Optional[str], limit: int):
    """获取“新增用户”可选来源渠道。

    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :param keyword: 渠道关键词
    :param limit: 返回数量限制
    :return: 渠道列表
    """
    ensure_admin_page_permission(current_admin, "users")
    limit = min(max(int(limit or 20), 1), 50)
    stmt = select(Channel).where(Channel.status == "ACTIVE")
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Channel.channel_name.like(pattern), Channel.sales_name.like(pattern)))
    if _is_business_consultant(current_admin):
        stmt = stmt.where(Channel.admin_user_id == current_admin.id)
    channels = (await db.execute(stmt.order_by(Channel.id.asc()).limit(limit))).scalars().all()
    return [serialize_channel_landing(item) for item in channels]

async def _create_channel(db: AsyncSession, current_admin: Admin, req: ChannelCreateRequest):
    ensure_admin_page_permission(current_admin, "channels")
    channel_name = normalize_channel_name(req.channel_name)
    sales_name = req.sales_name.strip()
    if not sales_name:
        raise HTTPException(status_code=400, detail="请填写业务员姓名")
    exists = (await db.execute(select(Channel).where(Channel.channel_name == channel_name))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="渠道名称已存在")
    invite_code = (req.invite_code or "").strip().lower()
    if not invite_code:
        invite_code = await _generate_unique_channel_invite_code(db, 16)
    else:
        invite_code_exists = (await db.execute(select(Channel).where(Channel.invite_code == invite_code))).scalar_one_or_none()
        if invite_code_exists:
            raise HTTPException(status_code=400, detail="渠道邀请码已存在")
    advisor = await _resolve_business_advisor_by_id(db, req.admin_user_id)
    channel = Channel(
        channel_name=channel_name,
        invite_code=invite_code,
        sales_name=sales_name,
        status=normalize_channel_status(req.status),
        note=(req.note or "").strip() or None,
        admin_user_id=advisor.id,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return serialize_channel(channel, advisor)

async def _update_channel(db: AsyncSession, current_admin: Admin, channel_id: int, req: ChannelUpdateRequest):
    ensure_admin_page_permission(current_admin, "channels")
    channel = (
        await db.execute(
            select(Channel)
            .options(joinedload(Channel.users).joinedload(User.loans))
            .where(Channel.id == channel_id)
        )
    ).unique().scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    payload = req.model_dump(exclude_unset=True)
    if "sales_name" in payload and payload["sales_name"] is not None:
        sales_name = payload["sales_name"].strip()
        if not sales_name:
            raise HTTPException(status_code=400, detail="请填写业务员姓名")
        channel.sales_name = sales_name
    if "status" in payload and payload["status"] is not None:
        channel.status = normalize_channel_status(payload["status"])
    if "note" in payload:
        channel.note = (payload["note"] or "").strip() or None
    if "admin_user_id" in payload and payload["admin_user_id"] is not None:
        advisor = await _resolve_business_advisor_by_id(db, int(payload["admin_user_id"]))
        channel.admin_user_id = advisor.id
    if not (channel.invite_code or "").strip():
        # 兼容历史空邀请码数据：编辑保存时自动补齐，避免专属链接不可用
        channel.invite_code = await _generate_unique_channel_invite_code(db, 16)
    await db.commit()
    await db.refresh(channel)
    advisor = None
    if channel.admin_user_id:
        advisor = (await db.execute(select(Admin).where(Admin.id == channel.admin_user_id))).scalar_one_or_none()
    return serialize_channel(channel, advisor)


async def _get_business_advisors(db: AsyncSession, current_admin: Admin, keyword: Optional[str], limit: int):
    ensure_admin_page_permission(current_admin, "channels")
    limit = min(max(limit, 1), 50)
    stmt = select(Admin)
    if keyword:
        text = keyword.strip()
        if text:
            if text.isdigit():
                stmt = stmt.where(or_(Admin.id == int(text), Admin.username.like(f"%{text}%")))
            else:
                stmt = stmt.where(Admin.username.like(f"%{text}%"))
    admins = (await db.execute(stmt.order_by(Admin.id.desc()).limit(limit * 3))).scalars().all()
    items: list[BusinessAdvisorItemResponse] = []
    for admin in admins:
        if _is_business_consultant(admin):
            items.append(BusinessAdvisorItemResponse(id=admin.id, username=admin.username))
            if len(items) >= limit:
                break
    return items

async def _get_products(db: AsyncSession, current_admin: Admin, keyword: Optional[str], is_active: Optional[bool], skip: int, limit: int):
    ensure_admin_page_permission(current_admin, "products")
    limit = min(max(limit, 1), 100)
    stmt = select(Product)
    if keyword:
        stmt = stmt.where(Product.name.like(f"%{keyword.strip()}%"))
    if is_active is not None:
        stmt = stmt.where(Product.is_active.is_(is_active))
    total = (await db.scalar(select(func.count()).select_from(stmt.subquery()))) or 0
    items = (
        await db.execute(stmt.order_by(Product.updated_at.desc(), Product.id.desc()).offset(skip).limit(limit))
    ).scalars().all()
    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [serialize_product(item) for item in items],
    }

async def _create_product(db: AsyncSession, current_admin: Admin, req: ProductCreateRequest):
    ensure_admin_page_permission(current_admin, "products")
    payment_amount = resolve_product_payment_amount(req.ecard_face_value, req.rights_price, req.payment_amount)
    product = Product(
        name=req.name.strip(),
        ecard_face_value=round_money(req.ecard_face_value),
        rights_price=round_money(req.rights_price),
        rights_title=req.rights_title.strip(),
        rights_desc=(req.rights_desc or "").strip() or None,
        term_days=req.term_days,
        payment_amount=payment_amount,
        is_active=req.is_active,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return serialize_product(product)

async def _update_product(db: AsyncSession, current_admin: Admin, product_id: int, req: ProductUpdateRequest):
    ensure_admin_page_permission(current_admin, "products")
    product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    payload = req.model_dump(exclude_unset=True)
    if "name" in payload and payload["name"] is not None:
        product.name = payload["name"].strip()
    if "ecard_face_value" in payload and payload["ecard_face_value"] is not None:
        product.ecard_face_value = round_money(payload["ecard_face_value"])
    if "rights_price" in payload and payload["rights_price"] is not None:
        product.rights_price = round_money(payload["rights_price"])
    if "rights_title" in payload and payload["rights_title"] is not None:
        product.rights_title = payload["rights_title"].strip()
    if "rights_desc" in payload:
        product.rights_desc = (payload["rights_desc"] or "").strip() or None
    if "term_days" in payload and payload["term_days"] is not None:
        product.term_days = payload["term_days"]
    if "is_active" in payload and payload["is_active"] is not None:
        product.is_active = bool(payload["is_active"])
    if "payment_amount" in payload and payload["payment_amount"] is not None:
        product.payment_amount = round_money(payload["payment_amount"])
    elif "ecard_face_value" in payload or "rights_price" in payload:
        product.payment_amount = resolve_product_payment_amount(product.ecard_face_value, product.rights_price)
    await db.commit()
    await db.refresh(product)
    return serialize_product(product)

async def _get_ecard_pool(db: AsyncSession, current_admin: Admin, keyword: Optional[str], status: Optional[str], face_value: Optional[float], skip: int, limit: int):
    ensure_admin_page_permission(current_admin, "ecard-pool")
    limit = min(max(limit, 1), 100)
    stmt = select(EcardPool)
    if keyword:
        stmt = stmt.where(EcardPool.account.like(f"%{keyword.strip()}%"))
    if status and status != "ALL":
        upper_status = status.upper()
        if upper_status not in ECARD_POOL_STATUSES:
            raise HTTPException(status_code=400, detail="卡池状态非法")
        stmt = stmt.where(EcardPool.status == upper_status)
    if face_value is not None:
        stmt = stmt.where(EcardPool.face_value == round_money(face_value))
    total = (await db.scalar(select(func.count()).select_from(stmt.subquery()))) or 0
    items = (
        await db.execute(stmt.order_by(EcardPool.expires_at.asc(), EcardPool.id.desc()).offset(skip).limit(limit))
    ).scalars().all()
    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [serialize_ecard_pool_item(item) for item in items],
    }

async def _create_ecard_pool_item(db: AsyncSession, current_admin: Admin, req: EcardPoolCreateRequest):
    ensure_admin_page_permission(current_admin, "ecard-pool")
    account = req.account.strip()
    if (await db.execute(select(EcardPool).where(EcardPool.account == account))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="卡号已存在")
    item = EcardPool(
        account=account,
        password=req.password.strip(),
        face_value=round_money(req.face_value),
        expires_at=req.expires_at,
        status="AVAILABLE",
        note=(req.note or "").strip() or None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return serialize_ecard_pool_item(item)

def _parse_upload_expiration(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("有效期不能为空")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            raise ValueError("有效期格式必须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
    raise ValueError("有效期格式错误")

def _load_excel_rows(upload_file: UploadFile):
    content = upload_file.file.read()
    upload_file.file.close()
    filename = upload_file.filename.lower()
    rows = []
    if filename.endswith(".xlsx"):
        workbook = load_workbook(BytesIO(content), data_only=True)
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=2, max_col=4, values_only=True):
            rows.append(list(row))
    elif filename.endswith(".xls"):
        workbook = xlrd.open_workbook(file_contents=content)
        sheet = workbook.sheet_by_index(0)
        for row_idx in range(1, sheet.nrows):
            row_values = []
            for col_idx in range(4):
                cell = sheet.cell(row_idx, col_idx)
                if col_idx == 3 and cell.ctype == xlrd.XL_CELL_DATE:
                    row_values.append(xlrd.xldate_as_datetime(cell.value, workbook.datemode))
                else:
                    row_values.append(cell.value)
            rows.append(row_values)
    else:
        raise HTTPException(status_code=400, detail="仅支持 xls 或 xlsx 文件")
    return rows

async def _upload_ecard_pool_items(db: AsyncSession, file: UploadFile, current_admin: Admin):
    ensure_admin_page_permission(current_admin, "ecard-pool")
    rows = _load_excel_rows(file)
    if not rows:
        raise HTTPException(status_code=400, detail="上传文件内容不能为空")

    upload_accounts = [str(row[0]).strip() for row in rows if row and row[0] is not None]
    existing_accounts = set()
    if upload_accounts:
        existing_accounts = set(
            (await db.execute(select(EcardPool.account).where(EcardPool.account.in_(upload_accounts)))).scalars().all()
        )
    created = 0
    errors = []
    seen_accounts = set()

    for index, row in enumerate(rows, start=2):
        account = (row[0] or "").strip() if len(row) >= 1 else ""
        password = (row[1] or "").strip() if len(row) >= 2 else ""
        face_value = row[2] if len(row) >= 3 else None
        expires_at = row[3] if len(row) >= 4 else None

        if not account and not password and not face_value and not expires_at:
            continue
        if not account:
            errors.append({"row": index, "reason": "卡号不能为空"})
            continue
        if not password:
            errors.append({"row": index, "reason": "密码不能为空"})
            continue
        if account in seen_accounts:
            errors.append({"row": index, "reason": "文件中存在重复卡号"})
            continue
        if account in existing_accounts:
            errors.append({"row": index, "reason": "卡号已存在"})
            continue

        try:
            face_value = float(face_value)
            if face_value <= 0:
                raise ValueError
        except Exception:
            errors.append({"row": index, "reason": "面额必须为正数"})
            continue

        try:
            expires_at = _parse_upload_expiration(expires_at)
        except ValueError as exc:
            errors.append({"row": index, "reason": str(exc)})
            continue

        item = EcardPool(
            account=account,
            password=password,
            face_value=round_money(face_value),
            expires_at=expires_at,
            status="AVAILABLE",
        )
        db.add(item)
        seen_accounts.add(account)
        created += 1

    await db.commit()
    return {
        "created": created,
        "errors": errors,
    }

async def _update_ecard_pool_item(db: AsyncSession, current_admin: Admin, item_id: int, req: EcardPoolUpdateRequest):
    ensure_admin_page_permission(current_admin, "ecard-pool")
    item = (await db.execute(select(EcardPool).where(EcardPool.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="卡池记录不存在")

    payload = req.model_dump(exclude_unset=True)
    if "status" in payload and payload["status"] is not None:
        next_status = payload["status"].upper()
        if next_status not in ECARD_POOL_STATUSES:
            raise HTTPException(status_code=400, detail="卡池状态非法")
        if item.status == "ASSIGNED" and next_status != "ASSIGNED":
            raise HTTPException(status_code=400, detail="已发放卡不可手工变更状态")
        item.status = next_status
    if "note" in payload:
        item.note = (payload["note"] or "").strip() or None
    if "expires_at" in payload and payload["expires_at"] is not None:
        item.expires_at = payload["expires_at"]

    await db.commit()
    await db.refresh(item)
    return serialize_ecard_pool_item(item)

async def _review_loan(db: AsyncSession, current_admin: Admin, loan_id: int, req: LoanReviewRequest):
    ensure_admin_page_permission(current_admin, "applications")
    loan = (
        await db.execute(
            select(Loan)
            .options(joinedload(Loan.owner), joinedload(Loan.review_admin))
            .where(Loan.id == loan_id)
        )
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")
    if loan.status in {"WITHDRAWING", "DISBURSED", "OVERDUE", "SETTLED"}:
        raise HTTPException(status_code=400, detail="当前订单已进入发卡/付款流程，不能重新审批")

    await assign_review_admin_if_needed_async(db, loan)
    if not is_super_admin(current_admin):
        if int(loan.review_admin_id or 0) != int(current_admin.id):
            raise HTTPException(status_code=403, detail="仅可处理分配给你的审批订单")

    owner = loan.owner
    if req.approved:
        if req.credit_limit is None:
            raise HTTPException(status_code=400, detail="请填写信用额度")
        approved_credit_limit = round_money(req.credit_limit)

        loan.status = "APPROVED"
        loan.approved_credit_limit = approved_credit_limit
        loan.credit_limit = approved_credit_limit
        loan.fee_rate = DEFAULT_FEE_RATE
        loan.fee_amount = 0
        loan.term_days = None
        loan.product_term_days = None
        loan.review_note = (req.review_note or "后台已完成授信审批").strip()
        loan.approved_at = datetime.now()
        loan.due_date = None
        loan.disbursed_at = None
        loan.penalty_amount = 0
        loan.repaid_amount = 0
        loan.reduction_amount = 0
        loan.paid_penalty_amount = 0
        loan.reduced_penalty_amount = 0
        loan.reminder_count = 0
        loan.last_reminded_at = None
        loan.collection_count = 0
        loan.last_collection_at = None
        loan.collection_note = None
        loan.collection_admin_id = None
        loan.collection_transferred_at = None
        loan.repay_attempt_count = 0
        loan.product_id = None
        loan.product_name = None
        loan.rights_title = None
        loan.rights_desc = None
        loan.rights_price = 0
        loan.ecard_face_value = 0
        loan.product_total_price = 0
        loan.ecard_account = None
        loan.ecard_password = None
        loan.ecard_expires_at = None
        owner.approved_limit = int(approved_credit_limit)

        detail = (
            f"审批通过；授信额度 {approved_credit_limit:.2f} 元；"
            f"用户可在商品列表中下单并消耗信用额度；备注：{loan.review_note}"
        )
        title = "后台审批通过"
        event_type = "ADMIN_APPROVED"
    else:
        loan.status = "REJECTED"
        loan.credit_limit = 0
        loan.approved_credit_limit = 0
        loan.fee_rate = DEFAULT_FEE_RATE
        loan.fee_amount = 0
        loan.term_days = None
        loan.product_term_days = None
        loan.review_note = (req.review_note or "暂未通过当前授信审核").strip()
        loan.approved_at = None
        loan.due_date = None
        loan.disbursed_at = None
        loan.penalty_amount = 0
        loan.repaid_amount = 0
        loan.reduction_amount = 0
        loan.paid_penalty_amount = 0
        loan.reduced_penalty_amount = 0
        loan.repay_attempt_count = 0
        loan.collection_admin_id = None
        loan.collection_transferred_at = None
        loan.product_id = None
        loan.product_name = None
        loan.rights_title = None
        loan.rights_desc = None
        loan.rights_price = 0
        loan.ecard_face_value = 0
        loan.product_total_price = 0
        loan.ecard_account = None
        loan.ecard_password = None
        loan.ecard_expires_at = None
        owner.approved_limit = 0

        detail = f"审批拒绝；备注：{loan.review_note}"
        title = "后台审批拒绝"
        event_type = "ADMIN_REJECTED"

    await log_user_event_async(
        db,
        user=owner,
        loan=loan,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type=event_type,
        title=title,
        detail=detail,
    )

    await db.commit()
    await db.refresh(loan)
    return serialize_loan(loan)

async def _update_loan(db: AsyncSession, current_admin: Admin, loan_id: int, req: LoanUpdateRequest):
    ensure_admin_page_permission(current_admin, "disbursements")
    loan = (
        await db.execute(select(Loan).options(joinedload(Loan.owner)).where(Loan.id == loan_id))
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")

    payload = req.model_dump(exclude_unset=True)
    if not payload:
        return serialize_loan(loan)

    owner = loan.owner
    change_messages = []
    previous_collection_note = loan.collection_note
    fee_rate_updated = False

    if "status" in payload:
        new_status = payload["status"]
        if new_status not in LOAN_STATUSES:
            raise HTTPException(status_code=400, detail="订单状态非法")

        loan.status = new_status
        change_messages.append(f"状态调整为 {new_status}")

        if new_status == "APPROVED" and loan.approved_at is None:
            loan.approved_at = datetime.now()
        if new_status == "REJECTED":
            owner.approved_limit = 0
            loan.approved_at = None
            loan.approved_credit_limit = 0
            loan.credit_limit = 0 if "credit_limit" not in payload else loan.credit_limit
            loan.fee_rate = DEFAULT_FEE_RATE
            loan.fee_amount = 0
            loan.repay_attempt_count = 0
            loan.product_id = None
            loan.product_name = None
            loan.rights_title = None
            loan.rights_desc = None
            loan.rights_price = 0
            loan.ecard_face_value = 0
            loan.product_total_price = 0
            loan.product_term_days = None
            loan.ecard_account = None
            loan.ecard_password = None
            loan.ecard_expires_at = None
        if new_status == "DISBURSED" and loan.disbursed_at is None:
            loan.disbursed_at = datetime.now()
        if new_status == "SETTLED":
            loan.penalty_amount = payload.get("penalty_amount", loan.penalty_amount)
            loan.repay_attempt_count = 0

    if "credit_limit" in payload:
        loan.credit_limit = float(payload["credit_limit"])
        if loan.status == "APPROVED":
            loan.approved_credit_limit = float(payload["credit_limit"])
        owner.approved_limit = int(payload["credit_limit"])
        change_messages.append(f"额度改为 {loan.credit_limit:.0f} 元")

    if "fee_rate" in payload:
        loan.fee_rate = normalize_fee_rate(payload["fee_rate"])
        fee_rate_updated = True
        change_messages.append(f"总费率改为 {loan.fee_rate * 100:.0f}%")

    if "term_days" in payload:
        loan.term_days = ensure_valid_term_days(payload["term_days"])
        change_messages.append(f"期限改为 {loan.term_days} 天")

    if "due_date" in payload and not loan.disbursed_at:
        loan.due_date = payload["due_date"]
        change_messages.append("重设还款日")

    if "penalty_amount" in payload:
        loan.penalty_amount = float(payload["penalty_amount"])
        change_messages.append(f"违约金改为 {loan.penalty_amount:.0f} 元")

    if "review_note" in payload:
        loan.review_note = payload["review_note"]
        change_messages.append("更新审批备注")

    if "collection_note" in payload:
        loan.collection_note = payload["collection_note"]
        change_messages.append("更新催收备注")

    if "credit_limit" in payload or fee_rate_updated:
        sync_loan_fee_fields(loan)

    if loan.disbursed_at and loan.term_days:
        loan.due_date = calculate_due_date(loan.disbursed_at, loan.term_days)
    elif loan.status == "DISBURSED" and loan.term_days:
        reference_time = datetime.now()
        loan.disbursed_at = reference_time
        loan.due_date = calculate_due_date(reference_time, loan.term_days)

    if (
        float(loan.repaid_amount or 0) + float(loan.reduction_amount or 0)
        > calculate_total_repayment_amount(loan) + 1e-6
    ):
        raise HTTPException(status_code=400, detail="已还款额与减免金额合计不能超过总还款额")

    if "collection_note" in payload:
        note_text = (payload.get("collection_note") or "").strip()
        previous_note = (previous_collection_note or "").strip()
        if note_text and note_text != previous_note:
            await log_user_event_async(
                db,
                user=owner,
                loan=loan,
                actor_type="ADMIN",
                operator_name=current_admin.username,
                event_type="ADMIN_COLLECTION_NOTE",
                title="新增催收备注",
                detail=note_text,
            )

    await log_user_event_async(
        db,
        user=owner,
        loan=loan,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_LOAN_UPDATED",
        title="后台更新订单信息",
        detail="；".join(change_messages),
    )

    await db.commit()
    await db.refresh(loan)
    return serialize_loan(loan)

async def _disburse_loan(db: AsyncSession, current_admin: Admin, loan_id: int, req: DisburseRequest):
    ensure_admin_page_permission(current_admin, "disbursements")
    loan = (
        await db.execute(select(Loan).options(joinedload(Loan.owner)).where(Loan.id == loan_id))
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")
    if loan.status != "WITHDRAWING":
        raise HTTPException(status_code=400, detail="仅待发卡订单支持发卡")

    term_days = ensure_valid_term_days(req.term_days or loan.product_term_days or loan.term_days)
    if not term_days:
        raise HTTPException(status_code=400, detail="请先确认账期天数")
    if round_money(loan.ecard_face_value or loan.credit_limit) <= 0:
        raise HTTPException(status_code=400, detail="请先确认商品信息")

    now = datetime.now()
    today = now.date()
    tomorrow_start = datetime(now.year, now.month, now.day) + timedelta(days=1)
    ecard_face_value = round_money(loan.ecard_face_value or loan.credit_limit)
    ecard_item = (
        await db.execute(
            select(EcardPool)
            .where(
                EcardPool.status == "AVAILABLE",
                EcardPool.face_value == ecard_face_value,
                EcardPool.expires_at >= tomorrow_start,
            )
            .order_by(EcardPool.expires_at.asc(), EcardPool.id.asc())
        )
    ).scalars().first()
    # 兜底校验：即使数据库比较存在时区/函数差异，也严格禁止“今天到期”的卡发放。
    if ecard_item and ecard_item.expires_at.date() <= today:
        ecard_item = None
    if not ecard_item:
        raise HTTPException(status_code=400, detail=f"卡池库存不足：未找到面额 {ecard_face_value:.2f} 元且有效的京东E卡")

    sync_loan_fee_fields(loan)
    disbursed_at = now
    loan.status = "DISBURSED"
    loan.term_days = term_days
    loan.product_term_days = term_days
    loan.credit_limit = ecard_face_value
    if not loan.product_total_price:
        loan.product_total_price = round_money(loan.credit_limit + (loan.rights_price or loan.fee_amount))
    loan.disbursed_at = disbursed_at
    loan.due_date = calculate_due_date(disbursed_at, term_days)
    loan.penalty_amount = 0
    loan.repaid_amount = 0
    loan.reduction_amount = 0
    loan.paid_penalty_amount = 0
    loan.reduced_penalty_amount = 0
    loan.collection_admin_id = None
    loan.collection_transferred_at = None
    loan.ecard_account = ecard_item.account
    loan.ecard_password = ecard_item.password
    loan.ecard_expires_at = ecard_item.expires_at

    ecard_item.status = "ASSIGNED"
    ecard_item.loan_id = loan.id
    ecard_item.assigned_at = now

    await ensure_installment_records_async(db, loan)
    await create_disbursement_transaction_async(
        db,
        loan,
        operator_name=current_admin.username,
        note="后台确认发放京东E卡",
    )

    await log_user_event_async(
        db,
        user=loan.owner,
        loan=loan,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_CARD_ISSUED",
        title="后台确认发卡",
        detail=(
            f"发卡商品：{loan.product_name or '未命名商品'}；"
            f"京东E卡面值 {loan.credit_limit:.2f} 元；"
            f"旅游权益 {round_money(loan.rights_price):.2f} 元；"
            f"支付金额 {round_money(loan.product_total_price):.2f} 元；"
            f"账期 {loan.term_days} 天；"
            f"到期日 {loan.due_date.strftime('%Y-%m-%d')}；"
            f"卡池记录 #{ecard_item.id}。"
        ),
    )

    await db.commit()
    await db.refresh(loan)
    return {"msg": "发卡成功", "loan": serialize_loan(loan)}

async def _settle_loan(db: AsyncSession, current_admin: Admin, loan_id: int):
    ensure_admin_page_permission(current_admin, "financials")
    loan = (
        await db.execute(select(Loan).options(joinedload(Loan.owner)).where(Loan.id == loan_id))
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")
    if loan.status not in {"DISBURSED", "OVERDUE"}:
        raise HTTPException(status_code=400, detail="订单状态不支持结清")

    remaining_amount = calculate_remaining_repayment_amount(loan)
    if remaining_amount > 0:
        await register_repayment_async(
            db,
            loan,
            remaining_amount,
            operator_name=current_admin.username,
            note="后台一键结清补录剩余待还金额",
            transaction_type="SETTLEMENT",
        )
    sync_loan_repayment_state(loan)
    await log_user_event_async(
        db,
        user=loan.owner,
        loan=loan,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_SETTLED",
        title="后台确认结清",
        detail="后台已登记该订单完成还款结清。",
    )

    await db.commit()
    return {"msg": "结清成功"}

async def _finance_reconcile_loan(
    db: AsyncSession,
    current_admin: Admin,
    loan_id: int,
    req: LoanFinanceReconcileRequest,
):
    ensure_admin_page_permission(current_admin, "financials")
    loan = (
        await db.execute(select(Loan).options(joinedload(Loan.owner)).where(Loan.id == loan_id))
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")
    if loan.status not in {"DISBURSED", "OVERDUE"}:
        raise HTTPException(status_code=400, detail="当前订单暂不支持财务平账")

    received_amount = round(float(req.received_amount or 0), 2)
    reduction_amount = round(float(req.reduction_amount or 0), 2)
    note = (req.note or "").strip()
    if received_amount <= 0 and reduction_amount <= 0:
        raise HTTPException(status_code=400, detail="请填写登记收款或减免金额")

    total_amount = calculate_total_repayment_amount(loan)
    next_repaid_amount = round(float(loan.repaid_amount or 0) + received_amount, 2)
    next_reduction_amount = round(float(loan.reduction_amount or 0) + reduction_amount, 2)
    if next_repaid_amount + next_reduction_amount > total_amount + 1e-6:
        raise HTTPException(status_code=400, detail="收款金额与减免金额累计不能超过总还款额")

    await ensure_installment_records_async(db, loan)

    if received_amount > 0:
        await register_repayment_async(
            db,
            loan,
            received_amount,
            operator_name=current_admin.username,
            note=note or "后台登记收款",
        )

    if reduction_amount > 0:
        await register_reduction_async(
            db,
            loan,
            reduction_amount,
            operator_name=current_admin.username,
            note=note or "后台登记减免",
        )

    remaining_amount = calculate_remaining_repayment_amount(loan)
    sync_loan_repayment_state(loan)

    detail_parts = []
    if received_amount > 0:
        detail_parts.append(f"登记收款 {received_amount:.2f} 元")
    if reduction_amount > 0:
        detail_parts.append(f"登记减免 {reduction_amount:.2f} 元")
    detail_parts.append(f"累计已还 {loan.repaid_amount:.2f} 元")
    detail_parts.append(f"累计减免 {loan.reduction_amount:.2f} 元")
    detail_parts.append(f"剩余待还 {remaining_amount:.2f} 元")
    if note:
        detail_parts.append(f"备注：{note}")
    if loan.status == "SETTLED":
        detail_parts.append("订单已完成平账结清")

    await log_user_event_async(
        db,
        user=loan.owner,
        loan=loan,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_FINANCE_RECONCILE",
        title="财务登记平账",
        detail="；".join(detail_parts),
    )

    await db.commit()
    await db.refresh(loan)
    return serialize_loan(loan)

async def _remind_loan(db: AsyncSession, current_admin: Admin, loan_id: int, req: LoanFollowUpRequest):
    ensure_admin_page_permission(current_admin, "repayments")
    loan = (
        await db.execute(
            select(Loan)
            .options(joinedload(Loan.owner), joinedload(Loan.review_admin))
            .where(Loan.id == loan_id)
        )
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")
    if loan.status not in {"DISBURSED", "OVERDUE"}:
        raise HTTPException(status_code=400, detail="当前订单不需要登记提醒")
    if is_collection_stage(loan):
        raise HTTPException(status_code=400, detail=f"该订单逾期已超过 {COLLECTION_TRANSFER_OVERDUE_DAYS} 天，请在催收管理处理")
    if not is_super_admin(current_admin):
        if int(loan.review_admin_id or 0) != int(current_admin.id):
            raise HTTPException(status_code=403, detail="仅可跟进分配给你的还款订单")

    loan.reminder_count = (loan.reminder_count or 0) + 1
    loan.last_reminded_at = datetime.now()
    note = (req.note or "已执行当日还款提醒").strip()

    await log_user_event_async(
        db,
        user=loan.owner,
        loan=loan,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_REMIND",
        title="登记还款提醒",
        detail=f"第 {loan.reminder_count} 次提醒；备注：{note}",
    )

    await db.commit()
    await db.refresh(loan)
    return serialize_loan(loan)

async def _collect_loan(db: AsyncSession, current_admin: Admin, loan_id: int, req: LoanFollowUpRequest):
    ensure_admin_page_permission(current_admin, "collections")
    loan = (
        await db.execute(
            select(Loan)
            .options(joinedload(Loan.owner), joinedload(Loan.collection_admin))
            .where(Loan.id == loan_id)
        )
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")
    if loan.status != "OVERDUE":
        raise HTTPException(status_code=400, detail="仅逾期订单支持登记催收")
    if not is_collection_stage(loan):
        raise HTTPException(status_code=400, detail=f"逾期超过 {COLLECTION_TRANSFER_OVERDUE_DAYS} 天后才可进入催收")

    await assign_collection_admin_if_needed_async(db, loan)
    if not is_super_admin(current_admin):
        if int(loan.collection_admin_id or 0) != int(current_admin.id):
            raise HTTPException(status_code=403, detail="仅可跟进分配给你的催收订单")

    loan.collection_count = (loan.collection_count or 0) + 1
    loan.last_collection_at = datetime.now()
    loan.collection_note = (req.note or "已执行逾期催收").strip()

    await log_user_event_async(
        db,
        user=loan.owner,
        loan=loan,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_COLLECT",
        title="登记催收跟进",
        detail=f"第 {loan.collection_count} 次催收；备注：{loan.collection_note}",
    )

    await db.commit()
    await db.refresh(loan)
    return serialize_loan(loan)

async def _ack_repay_attempt(db: AsyncSession, current_admin: Admin, loan_id: int):
    ensure_any_admin_page_permission(current_admin, ("repayments", "collections"))
    loan = (
        await db.execute(
            select(Loan)
            .options(
                joinedload(Loan.owner),
                joinedload(Loan.review_admin),
                joinedload(Loan.collection_admin),
            )
            .where(Loan.id == loan_id)
        )
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")
    ensure_stage_access_for_admin(current_admin, loan)

    cleared_count = int(loan.repay_attempt_count or 0)
    if cleared_count > 0:
        loan.repay_attempt_count = 0
        await log_user_event_async(
            db,
            user=loan.owner,
            loan=loan,
            actor_type="ADMIN",
            operator_name=current_admin.username,
            event_type="ADMIN_REPAY_ATTEMPT_ACK",
            title="查看还款跟进",
            detail=f"后台查看跟进时已清除还款点击提醒 {cleared_count} 次。",
        )
        await db.commit()
        await db.refresh(loan)

    return {
        "loan_id": loan.id,
        "cleared_count": cleared_count,
        "repay_attempt_count": int(loan.repay_attempt_count or 0),
    }

async def _get_loan_assignees(db: AsyncSession, current_admin: Admin, stage: str):
    if not is_super_admin(current_admin):
        raise HTTPException(status_code=403, detail="仅超级管理员可查看可分配人员")

    normalized_stage = (stage or "").strip().lower()
    if normalized_stage not in {"review", "collection"}:
        raise HTTPException(status_code=400, detail="分配阶段参数非法")

    role_key = "REVIEW" if normalized_stage == "review" else "COLLECTION"
    assignees = await list_admins_by_role_async(db, role_key)
    return [{"id": item.id, "username": item.username} for item in assignees]

async def _assign_loan(db: AsyncSession, current_admin: Admin, loan_id: int, req: LoanAssignRequest):
    if not is_super_admin(current_admin):
        raise HTTPException(status_code=403, detail="仅超级管理员可手动改派订单")

    loan = (
        await db.execute(select(Loan).options(joinedload(Loan.owner)).where(Loan.id == loan_id))
    ).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")

    assignee = (await db.execute(select(Admin).where(Admin.id == req.admin_id))).scalar_one_or_none()
    if not assignee:
        raise HTTPException(status_code=404, detail="分配目标不存在")

    stage = (req.stage or "").strip().lower()
    if stage not in {"review", "collection"}:
        raise HTTPException(status_code=400, detail="分配阶段参数非法")

    role_key = "REVIEW" if stage == "review" else "COLLECTION"
    if not admin_has_role(assignee, role_key):
        raise HTTPException(status_code=400, detail=f"目标账号不是{('审核员' if role_key == 'REVIEW' else '催收员')}")

    if stage == "review":
        previous = loan.review_admin_id
        loan.review_admin_id = assignee.id
        title = "超管手动改派审核负责人"
        detail = f"审核负责人由 #{previous or '-'} 调整为 #{assignee.id}（{assignee.username}）"
    else:
        if not is_collection_stage(loan):
            raise HTTPException(status_code=400, detail=f"逾期超过 {COLLECTION_TRANSFER_OVERDUE_DAYS} 天后才可改派催收负责人")
        previous = loan.collection_admin_id
        loan.collection_admin_id = assignee.id
        if loan.collection_transferred_at is None:
            loan.collection_transferred_at = datetime.now()
        title = "超管手动改派催收负责人"
        detail = f"催收负责人由 #{previous or '-'} 调整为 #{assignee.id}（{assignee.username}）"

    await log_user_event_async(
        db,
        user=loan.owner,
        loan=loan,
        actor_type="ADMIN",
        operator_name=current_admin.username,
        event_type="ADMIN_ASSIGNMENT_UPDATED",
        title=title,
        detail=detail,
    )

    await db.commit()
    return {
        "loan_id": loan.id,
        "stage": stage,
        "assignee_id": assignee.id,
        "assignee_name": assignee.username,
    }

async def _get_admin_users(db: AsyncSession, current_admin: Admin, keyword: Optional[str], skip: int, limit: int):
    ensure_admin_page_permission(current_admin, "admin-users")
    limit = min(max(limit, 1), 100)

    stmt = select(Admin)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(Admin.username.like(pattern))

    total = (await db.scalar(select(func.count()).select_from(stmt.subquery()))) or 0
    admins = (
        await db.execute(stmt.order_by(Admin.created_at.desc(), Admin.id.desc()).offset(skip).limit(limit))
    ).scalars().all()
    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [serialize_admin_user(item, current_admin) for item in admins],
    }

async def _create_admin_user(db: AsyncSession, current_admin: Admin, req: AdminUserCreateRequest):
    ensure_admin_page_permission(current_admin, "admin-users")
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="请输入后台用户名")

    if (await db.execute(select(Admin).where(Admin.username == username))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="后台用户名已存在")

    roles, permissions = resolve_roles_and_permissions(req.roles, req.permissions)
    if not roles:
        raise HTTPException(status_code=400, detail="请至少勾选一个角色")

    admin = Admin(
        username=username,
        password_hash=get_password_hash(req.password),
        roles=serialize_admin_roles(roles),
        permissions=serialize_admin_permissions(permissions),
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return serialize_admin_user(admin, current_admin)

async def _update_admin_user(db: AsyncSession, current_admin: Admin, admin_id: int, req: AdminUserUpdateRequest):
    ensure_admin_page_permission(current_admin, "admin-users")
    admin = (await db.execute(select(Admin).where(Admin.id == admin_id))).scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="后台用户不存在")

    payload = req.model_dump(exclude_unset=True)
    if not payload:
        return serialize_admin_user(admin, current_admin)

    if "username" in payload and payload["username"] is not None:
        username = payload["username"].strip()
        if not username:
            raise HTTPException(status_code=400, detail="请输入后台用户名")
        duplicated = (
            await db.execute(select(Admin).where(Admin.username == username, Admin.id != admin_id))
        ).scalar_one_or_none()
        if duplicated:
            raise HTTPException(status_code=400, detail="后台用户名已存在")
        admin.username = username

    if "password" in payload and payload["password"]:
        admin.password_hash = get_password_hash(payload["password"])

    if "permissions" in payload:
        roles_input = payload.get("roles", None)
        roles, permissions = resolve_roles_and_permissions(roles_input, payload["permissions"])
        if not roles:
            raise HTTPException(status_code=400, detail="请至少勾选一个角色")
        admin.roles = serialize_admin_roles(roles)
        admin.permissions = serialize_admin_permissions(permissions)
    elif "roles" in payload:
        roles, permissions = resolve_roles_and_permissions(payload["roles"], None)
        if not roles:
            raise HTTPException(status_code=400, detail="请至少勾选一个角色")
        admin.roles = serialize_admin_roles(roles)
        admin.permissions = serialize_admin_permissions(permissions)

    await db.commit()
    await db.refresh(admin)
    return serialize_admin_user(admin, current_admin)

async def _delete_admin_user(db: AsyncSession, current_admin: Admin, admin_id: int):
    ensure_admin_page_permission(current_admin, "admin-users")
    admin = (await db.execute(select(Admin).where(Admin.id == admin_id))).scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="后台用户不存在")
    if admin.id == current_admin.id:
        raise HTTPException(status_code=400, detail="当前登录账号不允许删除")

    await db.delete(admin)
    await db.commit()
    return {"msg": "删除成功"}
