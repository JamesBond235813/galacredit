import asyncio
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Optional

import xlrd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy import func, or_, select
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
)
from app.schemas.channel import (
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

from app.services.admin_service import get_today_range, _get_ws_admin_by_token, _extract_ws_token, calculate_due_date, ensure_valid_term_days, serialize_admin_user, resolve_roles_and_permissions, ensure_admin_page_permission, ensure_any_admin_page_permission, resolve_loan_scope_permission, current_admin_roles, is_super_admin, ensure_stage_access_for_admin, serialize_loan, serialize_user_summary, serialize_user_detail, serialize_channel, round_money, mask_secret, resolve_product_payment_amount, serialize_product, serialize_ecard_pool_item, apply_loan_scope, build_loan_scope_filters, get_overdue_days_expr, get_loan_operating_metrics, round_cash_amount, build_project_cash_insights, _register_user, _reset_user_password, _get_loan_ledger, _get_user_detail, _get_risk_report, _get_channels, _create_channel, _update_channel, _get_products, _create_product, _update_product, _get_ecard_pool, _create_ecard_pool_item, _parse_upload_expiration, _load_excel_rows, _upload_ecard_pool_items, _update_ecard_pool_item, _review_loan, _update_loan, _disburse_loan, _settle_loan, _finance_reconcile_loan, _remind_loan, _collect_loan, _ack_repay_attempt, _get_loan_assignees, _assign_loan, _get_admin_users, _create_admin_user, _update_admin_user, _delete_admin_user
router = APIRouter()


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


























































@router.post("/login", response_model=AdminTokenResponse)
async def login(req: AdminLogin, db: AsyncSession = Depends(get_async_db)):
    admin = (await db.execute(select(Admin).where(Admin.username == req.username))).scalar_one_or_none()
    if not admin or not verify_password(req.password, admin.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=admin.username, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=AdminResponse)
async def get_me(current_admin: Admin = Depends(get_current_admin_async)):
    return serialize_admin_user(current_admin)


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    ensure_any_admin_page_permission(current_admin, ADMIN_STATS_PERMISSION_KEYS)
    today_start, tomorrow = get_today_range()
    roles = current_admin_roles(current_admin)
    is_admin = "ADMIN" in roles
    overdue_days_expr = func.datediff(func.current_date(), func.date(Loan.due_date))

    # 统计接口只读，避免请求路径执行分配写入导致与调度任务并发时出现锁等待。

    total_users = (await db.scalar(select(func.count(User.id)))) or 0
    today_new_users = (await db.scalar(select(func.count(User.id)).where(User.created_at >= today_start, User.created_at < tomorrow))) or 0
    today_applications = (
        await db.scalar(
            select(func.count(User.id)).where(
                User.application_submitted_at >= today_start,
                User.application_submitted_at < tomorrow,
            )
        )
    ) or 0
    reviewing_stmt = select(func.count(Loan.id)).where(Loan.status == "REVIEWING")
    if not is_admin and "REVIEW" in roles:
        reviewing_stmt = reviewing_stmt.where(Loan.review_admin_id == current_admin.id)
    reviewing_loans = (await db.scalar(reviewing_stmt)) or 0
    approved_loans = (await db.scalar(select(func.count(Loan.id)).where(Loan.status == "APPROVED"))) or 0
    withdrawing_loans = (await db.scalar(select(func.count(Loan.id)).where(Loan.status == "WITHDRAWING"))) or 0
    disbursed_loans = (await db.scalar(select(func.count(Loan.id)).where(Loan.status == "DISBURSED"))) or 0
    due_today_loans = (
        await db.scalar(
            select(func.count(Loan.id)).where(
                Loan.status.in_(["DISBURSED", "OVERDUE"]),
                Loan.due_date >= today_start,
                Loan.due_date < tomorrow,
            )
        )
    ) or 0
    due_today_users = (
        await db.scalar(
            select(func.count(func.distinct(Loan.user_id))).where(
                Loan.status.in_(["DISBURSED", "OVERDUE"]),
                Loan.due_date >= today_start,
                Loan.due_date < tomorrow,
            )
        )
    ) or 0
    overdue_stmt = select(func.count(Loan.id)).where(Loan.status == "OVERDUE")
    if not is_admin and "COLLECTION" in roles:
        overdue_stmt = overdue_stmt.where(
            Loan.collection_admin_id == current_admin.id,
            Loan.due_date.isnot(None),
            overdue_days_expr > COLLECTION_TRANSFER_OVERDUE_DAYS,
        )
    overdue_loans = (await db.scalar(overdue_stmt)) or 0
    today_disbursed_amount = (
        await db.scalar(
            select(func.coalesce(func.sum(Loan.credit_limit), 0)).where(
                Loan.disbursed_at >= today_start,
                Loan.disbursed_at < tomorrow,
            )
        )
    ) or 0
    today_reminders = (
        await db.scalar(
            select(func.count(Loan.id)).where(
                Loan.last_reminded_at >= today_start,
                Loan.last_reminded_at < tomorrow,
            )
        )
    ) or 0
    today_collections = (
        await db.scalar(
            select(func.count(Loan.id)).where(
                Loan.last_collection_at >= today_start,
                Loan.last_collection_at < tomorrow,
            )
        )
    ) or 0
    repay_attempt_stmt = select(func.coalesce(func.sum(Loan.repay_attempt_count), 0)).where(
        or_(
            Loan.status == "DISBURSED",
            (Loan.status == "OVERDUE") & Loan.due_date.isnot(None) & (overdue_days_expr <= COLLECTION_TRANSFER_OVERDUE_DAYS),
        )
    )
    if not is_admin and "REVIEW" in roles:
        repay_attempt_stmt = repay_attempt_stmt.where(Loan.review_admin_id == current_admin.id)
    repay_attempt_total = (await db.scalar(repay_attempt_stmt)) or 0

    return {
        "total_users": total_users,
        "today_new_users": today_new_users,
        "today_applications": today_applications,
        "reviewing_loans": reviewing_loans,
        "approved_loans": approved_loans,
        "withdrawing_loans": withdrawing_loans,
        "disbursed_loans": disbursed_loans,
        "due_today_loans": due_today_loans,
        "due_today_users": due_today_users,
        "repay_attempt_total": int(repay_attempt_total or 0),
        "overdue_loans": overdue_loans,
        "today_disbursed_amount": float(today_disbursed_amount),
        "today_reminders": today_reminders,
        "today_collections": today_collections,
    }


@router.websocket("/ws/stats")
async def admin_stats_ws(websocket: WebSocket, db: AsyncSession = Depends(get_async_db)):
    """通过 WebSocket 推送后台统计数据。

    :param websocket: WebSocket 连接
    :param db: 异步数据库会话
    :return: None
    """
    trace_id = websocket.headers.get((settings.TID_HEADER_NAME or "X-Trace-Id")) or new_trace_id()
    tid_token = set_trace_id(trace_id)
    try:
        await websocket.accept()
        token = _extract_ws_token(websocket)
        current_admin = await _get_ws_admin_by_token(db, token)
        if current_admin is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            ensure_any_admin_page_permission(current_admin, ADMIN_STATS_PERMISSION_KEYS)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            while True:
                payload = await get_stats(db=db, current_admin=current_admin)
                await websocket.send_json({"type": "admin_stats", "data": payload})
                await asyncio.sleep(ADMIN_STATS_WS_PUSH_SECONDS)
        except WebSocketDisconnect:
            return
    finally:
        reset_trace_id(tid_token)

@router.get("/repayment-stats", response_model=RepaymentStatsResponse)
async def get_repayment_stats(
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    ensure_any_admin_page_permission(current_admin, REPAYMENT_STATS_PERMISSION_KEYS)
    repayment_statuses = ["DISBURSED", "OVERDUE", "SETTLED"]
    loans = (
        await db.execute(select(Loan).options(joinedload(Loan.installments)).where(Loan.status.in_(repayment_statuses)))
    ).unique().scalars().all()

    receivable_user_count = len({loan.user_id for loan in loans})
    receivable_amount = round(sum(calculate_total_repayment_amount(loan) for loan in loans), 2)
    received_user_count = len({loan.user_id for loan in loans if float(loan.repaid_amount or 0) > 0})
    received_amount = round(sum(float(loan.repaid_amount or 0) for loan in loans), 2)
    reduction_amount = round(sum(float(loan.reduction_amount or 0) for loan in loans), 2)

    disbursed_amount = 0.0
    expected_interest_amount = 0.0
    expected_guarantee_fee_amount = 0.0
    expected_income_amount = 0.0
    realized_income_amount = 0.0
    outstanding_principal_amount = 0.0
    overdue_outstanding_amount = 0.0
    reduced_principal_amount = 0.0
    reduced_fee_amount = 0.0

    for loan in loans:
        metrics = get_loan_operating_metrics(loan)
        disbursed_amount += float(loan.credit_limit or 0)
        expected_interest_amount += metrics["expected_interest_amount"]
        expected_guarantee_fee_amount += metrics["expected_guarantee_fee_amount"]
        expected_income_amount += metrics["expected_income_amount"]
        realized_income_amount += metrics["realized_income_amount"]
        outstanding_principal_amount += metrics["principal_balance_amount"]
        reduced_principal_amount += metrics["reduced_principal_amount"]
        reduced_fee_amount += metrics["reduced_fee_amount"]

        if loan.status == "OVERDUE":
            overdue_outstanding_amount += metrics["remaining_amount"]

    repeat_borrow_subquery = (
        select(Loan.user_id).group_by(Loan.user_id).having(func.count(Loan.id) >= 2).subquery()
    )
    repeat_borrow_count = (await db.scalar(select(func.count()).select_from(repeat_borrow_subquery))) or 0

    repayment_rate = (float(received_amount) / float(receivable_amount) * 100) if receivable_amount else 0
    repeat_borrow_rate = (float(repeat_borrow_count) / float(receivable_user_count) * 100) if receivable_user_count else 0

    return {
        "receivable_user_count": int(receivable_user_count),
        "receivable_amount": round(float(receivable_amount), 2),
        "received_user_count": int(received_user_count),
        "received_amount": round(float(received_amount), 2),
        "repayment_rate": round(float(repayment_rate), 2),
        "repeat_borrow_count": int(repeat_borrow_count),
        "repeat_borrow_rate": round(float(repeat_borrow_rate), 2),
        "reduction_amount": round(float(reduction_amount), 2),
        "disbursed_amount": round(float(disbursed_amount), 2),
        "expected_interest_amount": round(float(expected_interest_amount), 2),
        "expected_guarantee_fee_amount": round(float(expected_guarantee_fee_amount), 2),
        "expected_income_amount": round(float(expected_income_amount), 2),
        "realized_income_amount": round(float(realized_income_amount), 2),
        "outstanding_principal_amount": round(float(outstanding_principal_amount), 2),
        "overdue_outstanding_amount": round(float(overdue_outstanding_amount), 2),
        "reduced_principal_amount": round(float(reduced_principal_amount), 2),
        "reduced_fee_amount": round(float(reduced_fee_amount), 2),
    }

@router.get("/project-cash-insights", response_model=ProjectCashInsightResponse)
async def get_project_cash_insights(
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    ensure_admin_page_permission(current_admin, "overview")
    today_start, tomorrow = get_today_range()
    loans = (
        await db.execute(
            select(Loan)
            .options(
                joinedload(Loan.owner).joinedload(User.source_channel),
                joinedload(Loan.installments),
            )
            .where(Loan.status.in_(["WITHDRAWING", "DISBURSED", "OVERDUE", "SETTLED"]))
        )
    ).unique().scalars().all()
    return await build_project_cash_insights(db, loans, today_start, tomorrow)

@router.get("/loans", response_model=PaginatedLoanResponse)
async def get_loans(
    status: Optional[str] = Query(None, description="订单状态"),
    phone: Optional[str] = Query(None, description="手机号/姓名/身份证号"),
    scope: Optional[str] = Query(None, description="业务筛选"),
    due_date_preset: Optional[str] = Query(None, description="还款日快捷筛选"),
    overdue_min_days: Optional[int] = Query(None, ge=1, description="最小逾期天数"),
    overdue_max_days: Optional[int] = Query(None, ge=1, description="最大逾期天数"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    permission_key = resolve_loan_scope_permission(scope, due_date_preset, status)
    if permission_key:
        ensure_admin_page_permission(current_admin, permission_key)
    else:
        ensure_any_admin_page_permission(current_admin, LOAN_PAGE_PERMISSION_KEYS)

    if due_date_preset and due_date_preset not in {"TODAY", "TOMORROW"}:
        raise HTTPException(status_code=400, detail="还款日快捷筛选参数非法")

    if (
        overdue_min_days is not None
        and overdue_max_days is not None
        and overdue_min_days > overdue_max_days
    ):
        raise HTTPException(status_code=400, detail="最小逾期天数不能大于最大逾期天数")

    limit = min(max(limit, 1), 100)
    # 列表接口只读，避免请求路径执行分配写入导致与调度任务并发时出现锁等待。

    stmt = (
        select(Loan)
        .options(
            joinedload(Loan.owner).joinedload(User.source_channel),
            joinedload(Loan.owner).joinedload(User.loans),
            joinedload(Loan.review_admin),
            joinedload(Loan.collection_admin),
        )
        .join(User, Loan.user_id == User.id)
    )

    if status and status != "ALL":
        stmt = stmt.where(Loan.status == status)

    if phone:
        keyword = f"%{phone.strip()}%"
        stmt = stmt.where(
            or_(
                User.phone.like(keyword),
                User.name.like(keyword),
                User.id_card_num.like(keyword),
            )
        )

    scope_filters = build_loan_scope_filters(scope)
    if scope_filters:
        stmt = stmt.where(*scope_filters)

    roles = current_admin_roles(current_admin)
    if "ADMIN" not in roles:
        if scope == "OVERDUE":
            if "COLLECTION" in roles:
                stmt = stmt.where(Loan.collection_admin_id == current_admin.id)
            elif "REVIEW" in roles:
                stmt = stmt.where(Loan.review_admin_id == current_admin.id)
        elif scope in {"REVIEWING", "REPAYMENTS"}:
            if "REVIEW" in roles:
                stmt = stmt.where(Loan.review_admin_id == current_admin.id)
        elif "REVIEW" in roles:
            stmt = stmt.where(Loan.review_admin_id == current_admin.id)

    if due_date_preset:
        today_start, tomorrow = get_today_range()
        day_start = today_start if due_date_preset == "TODAY" else tomorrow
        day_end = day_start + timedelta(days=1)
        stmt = stmt.where(
            Loan.due_date.isnot(None),
            Loan.due_date >= day_start,
            Loan.due_date < day_end,
        )

    if overdue_min_days is not None or overdue_max_days is not None:
        overdue_days_expr = get_overdue_days_expr()
        stmt = stmt.where(Loan.status == "OVERDUE", Loan.due_date.isnot(None))

        if overdue_min_days is not None:
            stmt = stmt.where(overdue_days_expr >= overdue_min_days)
        if overdue_max_days is not None:
            stmt = stmt.where(overdue_days_expr <= overdue_max_days)

    total = (await db.scalar(select(func.count()).select_from(stmt.subquery()))) or 0

    if scope in {"DUE_TODAY", "OVERDUE"} or due_date_preset in {"TODAY", "TOMORROW"}:
        loans = (
            await db.execute(stmt.order_by(Loan.due_date.asc(), Loan.created_at.desc()).offset(skip).limit(limit))
        ).unique().scalars().all()
    else:
        loans = (
            await db.execute(stmt.order_by(Loan.created_at.desc()).offset(skip).limit(limit))
        ).unique().scalars().all()

    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [serialize_loan(loan) for loan in loans],
    }

@router.get("/users", response_model=PaginatedUserResponse)
async def get_users(
    keyword: Optional[str] = Query(None, description="手机号/姓名/身份证"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    ensure_admin_page_permission(current_admin, "users")
    limit = min(max(limit, 1), 100)
    stmt = (
        select(User)
        .options(joinedload(User.loans), joinedload(User.source_channel))
        .outerjoin(Channel, User.source_channel_id == Channel.id)
    )

    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                User.phone.like(pattern),
                User.name.like(pattern),
                User.id_card_num.like(pattern),
                Channel.channel_name.like(pattern),
                Channel.sales_name.like(pattern),
            )
        )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.scalar(total_stmt)) or 0
    users = (
        await db.execute(stmt.order_by(User.created_at.desc()).offset(skip).limit(limit))
    ).unique().scalars().all()

    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [serialize_user_summary(user) for user in users],
    }




@router.post("/users")
async def register_user(
    req: RegisterUserRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """后台新增用户接口。

    :param req: 新增用户请求体
    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :return: 新增结果
    """
    return await _register_user(db, current_admin, req)




@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    req: ResetUserPasswordRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """后台重置用户密码接口。

    :param user_id: 用户ID
    :param req: 重置密码请求体
    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :return: 重置结果
    """
    return await _reset_user_password(db, current_admin, user_id, req)




@router.get("/loans/{loan_id}/ledger", response_model=LoanLedgerResponse)
async def get_loan_ledger(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_loan_ledger(db, current_admin, loan_id)




@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_user_detail(db, current_admin, user_id)




@router.post("/risk/report", response_model=RiskReportResponse)
async def get_risk_report(
    req: AdminRiskReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_risk_report(db, req,  current_admin)




@router.get("/channels", response_model=PaginatedChannelResponse)
async def get_channels(
    keyword: Optional[str] = Query(None, description="渠道名称/业务员"),
    status: Optional[str] = Query("ALL", description="渠道状态"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_channels(db, current_admin, keyword, status, skip, limit)




@router.post("/channels")
async def create_channel(
    req: ChannelCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _create_channel(db, current_admin, req)




@router.patch("/channels/{channel_id}")
async def update_channel(
    channel_id: int,
    req: ChannelUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _update_channel(db, current_admin, channel_id, req)




@router.get("/products", response_model=PaginatedProductResponse)
async def get_products(
    keyword: Optional[str] = Query(None, description="商品名称"),
    is_active: Optional[bool] = Query(None, description="是否上架"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_products(db, current_admin, keyword, is_active, skip, limit)




@router.post("/products")
async def create_product(
    req: ProductCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _create_product(db, current_admin, req)




@router.patch("/products/{product_id}")
async def update_product(
    product_id: int,
    req: ProductUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _update_product(db, current_admin, product_id, req)




@router.get("/ecard-pool", response_model=PaginatedEcardPoolResponse)
async def get_ecard_pool(
    keyword: Optional[str] = Query(None, description="卡号关键词"),
    status: Optional[str] = Query("ALL", description="卡状态"),
    face_value: Optional[float] = Query(None, description="面额"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_ecard_pool(db, current_admin, keyword, status, face_value, skip, limit)








@router.post("/ecard-pool")
async def create_ecard_pool_item(
    req: EcardPoolCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _create_ecard_pool_item(db, current_admin, req)




@router.post("/ecard-pool/batch-upload")
async def upload_ecard_pool_items(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _upload_ecard_pool_items(db, file,  current_admin)


@router.get("/ecard-pool/template")
async def download_ecard_pool_template(
    current_admin: Admin = Depends(get_current_admin_async),
):
    ensure_admin_page_permission(current_admin, "ecard-pool")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "E卡批量上传模板"
    sheet.append(["卡号", "密码", "面额", "有效期"])
    sheet.append(["1234567890123456", "password123", 100, "2028-04-20 23:59:59"])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ecard_pool_template.xlsx"},
    )




@router.patch("/ecard-pool/{item_id}")
async def update_ecard_pool_item(
    item_id: int,
    req: EcardPoolUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _update_ecard_pool_item(db, current_admin, item_id, req)




@router.post("/loans/{loan_id}/review")
async def review_loan(
    loan_id: int,
    req: LoanReviewRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _review_loan(db, current_admin, loan_id, req)




@router.patch("/loans/{loan_id}")
async def update_loan(
    loan_id: int,
    req: LoanUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _update_loan(db, current_admin, loan_id, req)




@router.post("/loans/{loan_id}/disburse")
async def disburse_loan(
    loan_id: int,
    req: DisburseRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _disburse_loan(db, current_admin, loan_id, req)




@router.post("/loans/{loan_id}/settle")
async def settle_loan(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _settle_loan(db, current_admin, loan_id)




@router.post("/loans/{loan_id}/finance-reconcile")
async def finance_reconcile_loan(
    loan_id: int,
    req: LoanFinanceReconcileRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _finance_reconcile_loan(db, current_admin, loan_id, req)




@router.post("/loans/{loan_id}/remind")
async def remind_loan(
    loan_id: int,
    req: LoanFollowUpRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _remind_loan(db, current_admin, loan_id, req)




@router.post("/loans/{loan_id}/collect")
async def collect_loan(
    loan_id: int,
    req: LoanFollowUpRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _collect_loan(db, current_admin, loan_id, req)




@router.post("/loans/{loan_id}/ack-repay-attempt", response_model=RepayAttemptAckResponse)
async def ack_repay_attempt(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _ack_repay_attempt(db, current_admin, loan_id)




@router.get("/loan-assignees", response_model=list[LoanAssigneeItemResponse])
async def get_loan_assignees(
    stage: str = Query(..., description="review | collection"),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_loan_assignees(db, current_admin, stage)




@router.post("/loans/{loan_id}/assign", response_model=LoanAssignmentResponse)
async def assign_loan(
    loan_id: int,
    req: LoanAssignRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _assign_loan(db, current_admin, loan_id, req)




@router.get("/admin-users", response_model=PaginatedAdminUserResponse)
async def get_admin_users(
    keyword: Optional[str] = Query(None, description="用户名"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_admin_users(db, current_admin, keyword, skip, limit)




@router.post("/admin-users", response_model=AdminUserItemResponse)
async def create_admin_user(
    req: AdminUserCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _create_admin_user(db, current_admin, req)




@router.patch("/admin-users/{admin_id}", response_model=AdminUserItemResponse)
async def update_admin_user(
    admin_id: int,
    req: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _update_admin_user(db, current_admin, admin_id, req)




@router.delete("/admin-users/{admin_id}")
async def delete_admin_user(
    admin_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _delete_admin_user(db, current_admin, admin_id)
