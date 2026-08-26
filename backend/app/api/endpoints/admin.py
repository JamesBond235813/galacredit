import json
import asyncio
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Optional
from uuid import uuid4

import xlrd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload

from app.api.deps import get_admin_by_token_async, get_current_admin_async
from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_async_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.trace import new_trace_id, reset_trace_id, set_trace_id
from app.core.exceptions import BizException
from app.models.admin import Admin
from app.models.channel import Channel
from app.models.ecard_pool import EcardPool
from app.models.loan import Loan
from app.models.loan_transaction import LoanTransaction
from app.models.product import Product
from app.models.purchase_contract import PurchaseContractSignature
from app.models.loan_mandate import LoanMandate
from app.models.compliance_rule import ComplianceRule
from app.models.momo_transaction import MomoTransaction
from app.models.user import User
from app.models.user_event import UserEvent
from app.models.ops_history import AdminLoginHistory, ConfigChangeHistory, MessageTemplate
from app.models.risk_decision import RiskDecision, RiskRuleHit, RiskPolicyVersion
from app.models.risk_expansion import RiskManualOverride, RiskDeviceSignal
from app.services.risk_policy import (
    activate_risk_policy_version,
    copy_risk_policy_version,
    create_risk_policy_version,
    disable_risk_policy_version,
    list_risk_policy_versions,
    normalize_risk_policy_config,
    serialize_risk_policy_version,
    update_risk_policy_version,
)
from app.services.risk_scoring import record_device_signal
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
    ComplianceRuleCreateRequest,
    AdminAuditLogItemResponse,
    PaginatedAdminAuditLogResponse,
    KycReviewItemResponse,
    PaginatedKycReviewResponse,
    KycReviewActionRequest,
    KycBatchReviewRequest,
    MonitoringSummaryResponse,
    MessageCenterResponse,
)
from app.schemas.channel import (
    BusinessAdvisorItemResponse,
    ChannelCreateRequest,
    ExclusiveLinksResponse,
    ChannelUpdateRequest,
    PaginatedChannelResponse,
)
from app.schemas.loan import (
    AdminStatsResponse,
    ApprovedCreditSetRequest,
    AvailableCreditAdjustRequest,
    DisburseRequest,
    EcardPoolCreateRequest,
    EcardPoolUpdateRequest,
    LoanAssigneeItemResponse,
    LoanAssignmentResponse,
    LoanAssignRequest,
    LoanLedgerResponse,
    LoanFinanceReconcileRequest,
    LoanExtensionRequest,
    LoanFollowUpRequest,
    ProjectCashInsightResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    RepayAttemptAckResponse,
    RepaymentStatsResponse,
    LoanReviewRequest,
    LoanUpdateRequest,
    OverdueDisplayRequest,
    OverdueFeeConfigCreateRequest,
    PaginatedOverdueFeeConfigResponse,
    PaginatedEcardPoolResponse,
    PaginatedProductResponse,
    PaginatedLoanResponse,
    PurchaseContractResponse,
)
from app.schemas.risk import (
    AdminRiskReportRequest,
    AdminRiskSingleReportRequest,
    CompositeRiskReportResponse,
    PaginatedRiskSingleReportHistoryResponse,
    RiskReportResponse,
    RiskPolicyVersionCreateRequest,
    RiskPolicyVersionItemResponse,
    RiskPolicyVersionListResponse,
    RiskPolicyVersionUpdateRequest,
)
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
from app.services.approved_credit_expiry import expire_unused_approved_credits
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
from app.services.admin_session import assign_admin_session
from app.services.loan_ws_notify import notify_loan_snapshot_changed
from app.services.purchase_contract import serialize_purchase_contract
from app.services.compliance import get_active_compliance_rule_async, serialize_compliance_rule
from app.services.upload_storage import build_upload_url, save_product_rights_image

from app.services.admin_service import get_today_range, _get_ws_admin_by_token, _extract_ws_token, calculate_due_date, ensure_valid_term_days, serialize_admin_user, resolve_roles_and_permissions, ensure_admin_page_permission, ensure_any_admin_page_permission, resolve_loan_scope_permission, current_admin_roles, is_super_admin, ensure_stage_access_for_admin, serialize_loan, serialize_user_summary, serialize_user_detail, serialize_channel, round_money, mask_secret, resolve_product_payment_amount, serialize_product, serialize_ecard_pool_item, apply_loan_scope, build_loan_scope_filters, get_overdue_days_expr, get_loan_operating_metrics, round_cash_amount, build_project_cash_insights, notify_admin_stats_changed, wait_admin_stats_changed, _is_business_consultant, apply_business_consultant_user_summary_status, _register_user, _reset_user_password, _change_admin_password, _get_loan_ledger, _get_user_detail, _get_user_ip_audit, _get_risk_report, _get_composite_risk_report, _query_single_risk_report, _get_single_risk_report_history, _get_single_risk_report_detail, _get_channels, _get_exclusive_links, _get_user_source_channels, _create_channel, _update_channel, _get_business_advisors, _get_products, _get_disbursement_failures, _create_product, _update_product, _get_ecard_pool, _create_ecard_pool_item, _parse_upload_expiration, _load_excel_rows, _upload_ecard_pool_items, _update_ecard_pool_item, _review_loan, _update_loan, _disburse_loan, _reject_card_loan, _reissue_card_loan, _close_card_reissue, _extend_loan, _adjust_available_credit, _set_approved_credit_limit, _update_overdue_display, _get_overdue_fee_configs, _create_overdue_fee_config, _get_blacklist_entries, _manual_blacklist_user, _remove_blacklist_user, _upload_blacklist, _settle_loan, _finance_reconcile_loan, _remind_loan, _collect_loan, _ack_repay_attempt, _get_loan_assignees, _assign_loan, _get_admin_users, _get_admin_audit_logs, _get_kyc_review_queue, _review_kyc_users, _get_monitoring_summary, _get_message_center, _create_admin_user, _update_admin_user, _delete_admin_user, _unlock_user_location_risk
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
    "CARD_REJECTED",
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
ADMIN_STATS_WS_PUSH_SECONDS = 15
REPAYMENT_STATUS_FILTERS = {
    "NOT_DUE",
    "DUE_TODAY",
    "OVERDUE",
    "UNPAID",
    "PARTIAL_PAID",
    "SETTLED",
}


def build_repayment_status_filters(repayment_status: Optional[str]):
    """构建还款管理页账单进度筛选条件。

    :param repayment_status: 前端传入的还款状态筛选值
    :return: SQLAlchemy 查询条件列表
    """
    value = (repayment_status or "").strip().upper()
    if not value or value == "ALL":
        return []
    if value not in REPAYMENT_STATUS_FILTERS:
        raise HTTPException(status_code=400, detail="还款状态筛选参数非法")

    today_start, tomorrow = get_today_range()
    repaid_amount = func.coalesce(Loan.repaid_amount, 0)
    if value == "NOT_DUE":
        return [
            Loan.status == "DISBURSED",
            or_(Loan.due_date.is_(None), Loan.due_date >= tomorrow),
        ]
    if value == "DUE_TODAY":
        return [
            Loan.status.in_(["DISBURSED", "OVERDUE"]),
            Loan.due_date >= today_start,
            Loan.due_date < tomorrow,
        ]
    if value == "OVERDUE":
        return [Loan.status == "OVERDUE"]
    if value == "UNPAID":
        return [Loan.status != "SETTLED", repaid_amount <= 0]
    if value == "PARTIAL_PAID":
        return [Loan.status != "SETTLED", repaid_amount > 0]
    if value == "SETTLED":
        return [Loan.status == "SETTLED"]
    return []


async def _notify_user_loan_snapshot_if_needed(db: AsyncSession, loan_id: int):
    loan = (await db.execute(select(Loan.user_id).where(Loan.id == loan_id))).first()
    if loan and loan[0]:
        await notify_loan_snapshot_changed(int(loan[0]))


























































@router.post("/login", response_model=AdminTokenResponse)
async def login(req: AdminLogin, db: AsyncSession = Depends(get_async_db)):
    admin = (await db.execute(select(Admin).where(Admin.username == req.username))).scalar_one_or_none()
    success = bool(admin and verify_password(req.password, admin.password_hash) and getattr(admin, "is_active", True))
    db.add(AdminLoginHistory(admin_id=admin.id if admin else 0, username=req.username, client_type=req.client_type or "WEB", success=success, failure_reason=None if success else "用户名、密码错误或账号已禁用"))
    await db.flush()
    if not success:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    session_id = uuid4().hex
    client_type = assign_admin_session(admin, session_id, req.client_type, datetime.now())
    await db.commit()
    access_token = create_access_token(
        subject=admin.username,
        expires_delta=access_token_expires,
        jti=session_id,
        client_id=client_type,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/admin-users/{admin_id}/login-history")
async def get_admin_login_history(admin_id: int, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    ensure_admin_page_permission(current_admin, "admin-users")
    rows = (await db.execute(select(AdminLoginHistory).where(AdminLoginHistory.admin_id == admin_id).order_by(AdminLoginHistory.created_at.desc()).offset(skip).limit(limit))).scalars().all()
    return {"items": [{"id": x.id, "username": x.username, "client_type": x.client_type, "success": x.success, "failure_reason": x.failure_reason, "created_at": x.created_at} for x in rows]}


@router.get("/me", response_model=AdminResponse)
async def get_me(current_admin: Admin = Depends(get_current_admin_async)):
    return serialize_admin_user(current_admin)


@router.post("/change-password")
async def change_password(
    req: AdminChangePasswordRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _change_admin_password(db, current_admin, req)


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
    ecard_pool_available_amount = (
        await db.scalar(
            select(func.coalesce(func.sum(EcardPool.face_value), 0)).where(
                EcardPool.status == "AVAILABLE",
                EcardPool.expires_at >= tomorrow,
            )
        )
    ) or 0
    ecard_pool_available_count = (
        await db.scalar(
            select(func.count(EcardPool.id)).where(
                EcardPool.status == "AVAILABLE",
                EcardPool.expires_at >= tomorrow,
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
        "ecard_pool_available_amount": float(ecard_pool_available_amount),
        "ecard_pool_available_count": int(ecard_pool_available_count or 0),
    }


@router.websocket("/ws/stats")
async def admin_stats_ws(websocket: WebSocket):
    """通过 WebSocket 推送后台统计数据。

    :param websocket: WebSocket 连接
    :return: None
    """
    trace_id = websocket.headers.get((settings.TID_HEADER_NAME or "X-Trace-Id")) or new_trace_id()
    tid_token = set_trace_id(trace_id)
    try:
        await websocket.accept()
        token = _extract_ws_token(websocket)
        async with AsyncSessionLocal() as auth_db:
            current_admin = await _get_ws_admin_by_token(auth_db, token)
        if current_admin is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            ensure_any_admin_page_permission(current_admin, ADMIN_STATS_PERMISSION_KEYS)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            last_version = -1
            while True:
                # 每次推送使用独立短会话，避免长连接复用同一事务快照导致统计读到旧数据。
                async with AsyncSessionLocal() as loop_db:
                    loop_admin = await _get_ws_admin_by_token(loop_db, token)
                    if loop_admin is None:
                        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                        return
                    payload = await get_stats(db=loop_db, current_admin=loop_admin)
                await websocket.send_json({"type": "admin_stats", "data": payload})
                last_version = await wait_admin_stats_changed(last_version, ADMIN_STATS_WS_PUSH_SECONDS)
        except WebSocketDisconnect:
            return
    finally:
        reset_trace_id(tid_token)

@router.get("/repayment-stats", response_model=RepaymentStatsResponse)
async def get_repayment_stats(
    due_date_preset: Optional[str] = Query(None, description="还款日快捷筛选"),
    repayment_status: Optional[str] = Query(None, description="还款状态筛选"),
    due_date_start: Optional[date] = Query(None, description="应还款开始日期"),
    due_date_end: Optional[date] = Query(None, description="应还款结束日期"),
    actual_repayment_start: Optional[date] = Query(None, description="实际还款开始日期"),
    actual_repayment_end: Optional[date] = Query(None, description="实际还款结束日期"),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    ensure_any_admin_page_permission(current_admin, REPAYMENT_STATS_PERMISSION_KEYS)
    filters = build_loan_scope_filters("REPAYMENTS")
    if (
        due_date_start is not None
        and due_date_end is not None
        and due_date_start > due_date_end
    ):
        raise HTTPException(status_code=400, detail="应还款开始日期不能晚于结束日期")
    if (
        actual_repayment_start is not None
        and actual_repayment_end is not None
        and actual_repayment_start > actual_repayment_end
    ):
        raise HTTPException(status_code=400, detail="实际还款开始日期不能晚于结束日期")
    if due_date_preset:
        if due_date_preset not in {"TODAY", "TOMORROW"}:
            raise HTTPException(status_code=400, detail="还款日筛选不正确")
        today_start, tomorrow = get_today_range()
        day_start = today_start if due_date_preset == "TODAY" else tomorrow
        day_end = tomorrow if due_date_preset == "TODAY" else tomorrow + timedelta(days=1)
        # 卡片统计必须与页面所选还款日区间保持一致，避免列表与摘要口径不一致。
        filters.extend([
            Loan.due_date >= day_start,
            Loan.due_date < day_end,
        ])
    filters.extend(build_repayment_status_filters(repayment_status))
    if due_date_start is not None:
        filters.append(Loan.due_date >= datetime.combine(due_date_start, datetime.min.time()))
    if due_date_end is not None:
        filters.append(Loan.due_date < datetime.combine(due_date_end + timedelta(days=1), datetime.min.time()))
    if actual_repayment_start is not None:
        filters.append(Loan.actual_repayment_date >= actual_repayment_start)
    if actual_repayment_end is not None:
        filters.append(Loan.actual_repayment_date <= actual_repayment_end)

    loans = (
        await db.execute(select(Loan).options(joinedload(Loan.installments)).where(*filters))
    ).unique().scalars().all()
    today_start, tomorrow = get_today_range()
    due_today_loans = [
        loan
        for loan in loans
        if loan.due_date and today_start <= loan.due_date < tomorrow
    ]
    due_today_user_count = len({loan.user_id for loan in due_today_loans})
    due_today_amount = round(sum(calculate_total_repayment_amount(loan) for loan in due_today_loans), 2)
    due_today_actual_repayment_loans = [
        loan
        for loan in due_today_loans
        if getattr(loan, "actual_repayment_date", None) == today_start.date()
    ]
    due_today_actual_repayment_user_count = len({loan.user_id for loan in due_today_actual_repayment_loans})
    due_today_actual_repayment_amount = round(
        sum(float(loan.repaid_amount or 0) for loan in due_today_actual_repayment_loans),
        2,
    )
    today_actual_repayment_loans = [
        loan
        for loan in loans
        if getattr(loan, "actual_repayment_date", None) == today_start.date()
    ]
    today_actual_repayment_user_count = len({loan.user_id for loan in today_actual_repayment_loans})
    today_actual_repayment_amount = round(
        sum(float(loan.repaid_amount or 0) for loan in today_actual_repayment_loans),
        2,
    )
    # 回款页只统计尚未转入催收阶段的逾期订单；超过 14 天的订单由催收页承接。
    overdue_filters = build_loan_scope_filters("REPAYMENTS") + [
        Loan.status == "OVERDUE",
        Loan.due_date.isnot(None),
    ]
    if due_date_start is not None:
        overdue_filters.append(Loan.due_date >= datetime.combine(due_date_start, datetime.min.time()))
    if due_date_end is not None:
        overdue_filters.append(Loan.due_date < datetime.combine(due_date_end + timedelta(days=1), datetime.min.time()))
    overdue_loans = (
        await db.execute(
            select(Loan)
            .options(joinedload(Loan.installments))
            .where(*overdue_filters)
        )
    ).unique().scalars().all()
    overdue_order_count = len(overdue_loans)
    overdue_user_count = len({loan.user_id for loan in overdue_loans})
    overdue_amount = round(sum(calculate_remaining_repayment_amount(loan) for loan in overdue_loans), 2)

    pending_repayment_loans = [
        loan
        for loan in loans
        if (
            loan.status == "DISBURSED"
            and loan.due_date
            and loan.due_date >= tomorrow
            and calculate_remaining_repayment_amount(loan) > 0
        )
    ]
    pending_repayment_user_count = len({loan.user_id for loan in pending_repayment_loans})
    pending_repayment_amount = round(
        sum(calculate_remaining_repayment_amount(loan) for loan in pending_repayment_loans),
        2,
    )
    settled_loans = [loan for loan in loans if loan.status == "SETTLED"]
    partial_repaid_unsettled_loans = [
        loan
        for loan in loans
        if (
            loan.status != "SETTLED"
            and float(loan.repaid_amount or 0) > 0
            and calculate_remaining_repayment_amount(loan) > 0
        )
    ]
    settled_user_count = len({loan.user_id for loan in settled_loans})
    partial_repaid_unsettled_user_count = len({loan.user_id for loan in partial_repaid_unsettled_loans})

    receivable_order_count = len(loans)
    receivable_user_count = len({loan.user_id for loan in loans})
    receivable_amount = round(sum(calculate_total_repayment_amount(loan) for loan in loans), 2)
    received_user_count = len({loan.user_id for loan in loans if float(loan.repaid_amount or 0) > 0})
    received_amount = round(sum(float(loan.repaid_amount or 0) for loan in loans), 2)
    other_fee_amount = round(sum(float(loan.other_fee_amount or 0) for loan in loans), 2)
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
        "receivable_order_count": int(receivable_order_count),
        "receivable_user_count": int(receivable_user_count),
        "receivable_amount": round(float(receivable_amount), 2),
        "received_user_count": int(received_user_count),
        "received_amount": round(float(received_amount), 2),
        "due_today_user_count": int(due_today_user_count),
        "due_today_amount": round(float(due_today_amount), 2),
        "due_today_actual_repayment_user_count": int(due_today_actual_repayment_user_count),
        "due_today_actual_repayment_amount": round(float(due_today_actual_repayment_amount), 2),
        "today_actual_repayment_user_count": int(today_actual_repayment_user_count),
        "today_actual_repayment_amount": round(float(today_actual_repayment_amount), 2),
        "overdue_order_count": int(overdue_order_count),
        "overdue_user_count": int(overdue_user_count),
        "overdue_amount": round(float(overdue_amount), 2),
        "pending_repayment_user_count": int(pending_repayment_user_count),
        "pending_repayment_amount": round(float(pending_repayment_amount), 2),
        "settled_user_count": int(settled_user_count),
        "partial_repaid_unsettled_user_count": int(partial_repaid_unsettled_user_count),
        "other_fee_amount": round(float(other_fee_amount), 2),
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
    repayment_status: Optional[str] = Query(None, description="还款状态筛选"),
    due_date_preset: Optional[str] = Query(None, description="还款日快捷筛选"),
    due_date_start: Optional[date] = Query(None, description="应还款开始日期"),
    due_date_end: Optional[date] = Query(None, description="应还款结束日期"),
    actual_repayment_start: Optional[date] = Query(None, description="实际还款开始日期"),
    actual_repayment_end: Optional[date] = Query(None, description="实际还款结束日期"),
    review_admin_id: Optional[int] = Query(None, ge=1, description="审核员ID"),
    relend_count: Optional[int] = Query(None, ge=0, description="复购次数"),
    relend_min_count: Optional[int] = Query(None, ge=0, description="最小复购次数"),
    overdue_min_days: Optional[int] = Query(None, ge=1, description="最小逾期天数"),
    overdue_max_days: Optional[int] = Query(None, ge=1, description="最大逾期天数"),
    takeover_pool: bool = Query(False, description="审核员查看可转入自己的审核中申请"),
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

    if relend_count is not None and relend_min_count is not None:
        raise HTTPException(status_code=400, detail="复购次数筛选参数不能同时使用")

    if (
        overdue_min_days is not None
        and overdue_max_days is not None
        and overdue_min_days > overdue_max_days
    ):
        raise HTTPException(status_code=400, detail="最小逾期天数不能大于最大逾期天数")
    if (
        due_date_start is not None
        and due_date_end is not None
        and due_date_start > due_date_end
    ):
        raise HTTPException(status_code=400, detail="应还款开始日期不能晚于结束日期")
    if (
        actual_repayment_start is not None
        and actual_repayment_end is not None
        and actual_repayment_start > actual_repayment_end
    ):
        raise HTTPException(status_code=400, detail="实际还款开始日期不能晚于结束日期")

    roles = current_admin_roles(current_admin)
    review_takeover_pool = False
    if takeover_pool:
        if (
            "ADMIN" not in roles
            and "REVIEW" in roles
            and scope == "REVIEWING"
            and status in (None, "ALL", "REVIEWING")
            and admin_has_permission(current_admin, "loan-review-takeover")
        ):
            review_takeover_pool = True
        else:
            raise HTTPException(status_code=403, detail="无权查看可转入申请")

    if scope == "REVIEWING":
        expired_count = await expire_unused_approved_credits(db, now=datetime.now())
        if expired_count:
            await notify_admin_stats_changed()

    limit = min(max(limit, 1), 100)
    # 列表接口只读，避免请求路径执行分配写入导致与调度任务并发时出现锁等待。

    stmt = (
        select(Loan)
        .options(
            joinedload(Loan.owner).joinedload(User.source_channel),
            joinedload(Loan.owner).joinedload(User.loans),
            joinedload(Loan.owner).selectinload(User.events),
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

    if review_admin_id:
        stmt = stmt.where(Loan.review_admin_id == review_admin_id)

    if relend_count is not None or relend_min_count is not None:
        prior_loan = aliased(Loan)
        # 与列表展示口径保持一致：统计当前订单之前已结清的历史订单数。
        relend_count_expr = (
            select(func.count(prior_loan.id))
            .where(
                prior_loan.user_id == Loan.user_id,
                prior_loan.status == "SETTLED",
                prior_loan.id < Loan.id,
            )
            .correlate(Loan)
            .scalar_subquery()
        )
        if relend_count is not None:
            stmt = stmt.where(relend_count_expr == relend_count)
        if relend_min_count is not None:
            stmt = stmt.where(relend_count_expr >= relend_min_count)

    scope_filters = build_loan_scope_filters(scope)
    if scope_filters:
        stmt = stmt.where(*scope_filters)
    repayment_status_filters = build_repayment_status_filters(repayment_status)
    if repayment_status_filters:
        stmt = stmt.where(*repayment_status_filters)
    if review_takeover_pool:
        # 审核转入池只开放审核中的申请，避免借此查看已通过/未通过或其他阶段订单。
        stmt = stmt.where(Loan.status == "REVIEWING")

    if "ADMIN" not in roles:
        if scope == "OVERDUE":
            if "COLLECTION" in roles:
                stmt = stmt.where(Loan.collection_admin_id == current_admin.id)
            elif "REVIEW" in roles:
                stmt = stmt.where(Loan.review_admin_id == current_admin.id)
        elif scope in {"REVIEWING", "REPAYMENTS"}:
            if "REVIEW" in roles and not review_takeover_pool:
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
    if due_date_start is not None:
        stmt = stmt.where(Loan.due_date >= datetime.combine(due_date_start, datetime.min.time()))
    if due_date_end is not None:
        stmt = stmt.where(Loan.due_date < datetime.combine(due_date_end + timedelta(days=1), datetime.min.time()))
    if actual_repayment_start is not None:
        stmt = stmt.where(Loan.actual_repayment_date >= actual_repayment_start)
    if actual_repayment_end is not None:
        stmt = stmt.where(Loan.actual_repayment_date <= actual_repayment_end)

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
    location_risk_blocked: Optional[bool] = Query(None, description="是否命中位置风控锁定"),
    deal_time_start: Optional[date] = Query(None, description="成交开始日期，仅业务顾问生效"),
    deal_time_end: Optional[date] = Query(None, description="成交结束日期，仅业务顾问生效"),
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

    if location_risk_blocked is not None:
        stmt = stmt.where(User.location_risk_blocked.is_(location_risk_blocked))

    if _is_business_consultant(current_admin):
        # 业务顾问只能查看归属到自己负责渠道的客户。
        stmt = stmt.where(Channel.admin_user_id == current_admin.id)
        if deal_time_start or deal_time_end:
            # 业务顾问成交日期口径：按用户首单成交时间（first_disbursed_at）筛选。
            first_deal_subquery = (
                select(
                    Loan.user_id.label("user_id"),
                    func.min(Loan.disbursed_at).label("first_disbursed_at"),
                )
                .where(Loan.disbursed_at.isnot(None))
                .group_by(Loan.user_id)
                .subquery()
            )
            stmt = stmt.join(first_deal_subquery, first_deal_subquery.c.user_id == User.id)
            if deal_time_start:
                start_at = datetime.combine(deal_time_start, datetime.min.time())
                stmt = stmt.where(first_deal_subquery.c.first_disbursed_at >= start_at)
            if deal_time_end:
                end_exclusive = datetime.combine(deal_time_end + timedelta(days=1), datetime.min.time())
                stmt = stmt.where(first_deal_subquery.c.first_disbursed_at < end_exclusive)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.scalar(total_stmt)) or 0
    users = (
        await db.execute(stmt.order_by(User.created_at.desc()).offset(skip).limit(limit))
    ).unique().scalars().all()

    items = [
        apply_business_consultant_user_summary_status(serialize_user_summary(user), current_admin)
        for user in users
    ]
    can_unlock_location_risk = admin_has_permission(current_admin, "user-location-risk-unlock")
    for item in items:
        item["can_unlock_location_risk"] = can_unlock_location_risk
    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": items,
    }


@router.get("/users/source-channels")
async def get_user_source_channels(
    keyword: Optional[str] = Query(None, description="渠道名称/业务员"),
    limit: int = Query(50, ge=1, le=50),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_user_source_channels(db, current_admin, keyword, limit)




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
    result = await _register_user(db, current_admin, req)
    await notify_admin_stats_changed()
    return result




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
    result = await _reset_user_password(db, current_admin, user_id, req)
    await notify_admin_stats_changed()
    return result


@router.post("/users/{user_id}/location-risk/unlock")
async def unlock_user_location_risk(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """后台解除用户位置风控锁定。

    :param user_id: 用户ID
    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :return: 解除结果
    """
    return await _unlock_user_location_risk(db, current_admin, user_id)




@router.get("/loans/{loan_id}/ledger", response_model=LoanLedgerResponse)
async def get_loan_ledger(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_loan_ledger(db, current_admin, loan_id)


@router.get("/loans/{loan_id}/purchase-contract", response_model=PurchaseContractResponse)
async def get_loan_purchase_contract(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    ensure_any_admin_page_permission(current_admin, ("users", "applications", "disbursements", "repayments", "collections", "financials"))
    loan = (await db.execute(select(Loan).where(Loan.id == loan_id))).scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="订单不存在")
    signature = (
        await db.execute(
            select(PurchaseContractSignature)
            .where(PurchaseContractSignature.loan_id == loan_id)
            .order_by(PurchaseContractSignature.signed_at.desc(), PurchaseContractSignature.id.desc())
        )
    ).scalars().first()
    if not signature:
        raise HTTPException(status_code=404, detail="暂无已签署购销合同")
    return serialize_purchase_contract(signature)


@router.get("/loans/{loan_id}/momo-mandate")
async def get_loan_momo_mandate(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """查询订单最近一份 MoMo 扣款授权快照。

    :param loan_id: 贷款订单ID
    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :return: 授权记录
    """
    ensure_any_admin_page_permission(current_admin, ("users", "applications", "disbursements", "repayments", "collections", "financials"))
    mandate = (
        await db.execute(
            select(LoanMandate)
            .where(LoanMandate.loan_id == loan_id)
            .order_by(LoanMandate.signed_at.desc(), LoanMandate.id.desc())
        )
    ).scalars().first()
    if not mandate:
        raise HTTPException(status_code=404, detail="暂无 MoMo 扣款授权")
    return {
        "id": mandate.id,
        "loan_id": mandate.loan_id,
        "user_id": mandate.user_id,
        "provider": mandate.provider,
        "mandate_reference": mandate.mandate_reference,
        "status": mandate.status,
        "consent_version": mandate.consent_version,
        "consent_content": mandate.consent_content,
        "phone": mandate.phone,
        "signed_at": mandate.signed_at,
        "revoked_at": mandate.revoked_at,
    }




@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_user_detail(db, current_admin, user_id)


@router.get("/users/{user_id}/ip-audit")
async def get_user_ip_audit(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_user_ip_audit(db, current_admin, user_id)




@router.post("/risk/report", response_model=RiskReportResponse)
async def get_risk_report(
    req: AdminRiskReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_risk_report(db, req,  current_admin)


@router.post("/risk/composite-report", response_model=CompositeRiskReportResponse)
async def get_composite_risk_report(
    req: AdminRiskReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_composite_risk_report(db, req, current_admin)


@router.post("/risk/single-report", response_model=CompositeRiskReportResponse)
async def query_single_risk_report(
    req: AdminRiskSingleReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """单查 GalaCredit 风控报告。

    :param req: 单查三要素
    :param db: 异步数据库会话
    :param current_admin: 当前后台用户
    :return: GalaCredit 风险报告
    """
    return await _query_single_risk_report(db, req, current_admin)


@router.get("/risk/single-reports", response_model=PaginatedRiskSingleReportHistoryResponse)
async def get_single_risk_report_history(
    keyword: Optional[str] = Query(None, description="姓名/手机号/身份证号"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """获取风控报告单查历史。

    :param keyword: 客户三要素关键词
    :param skip: 跳过条数
    :param limit: 返回条数
    :param db: 异步数据库会话
    :param current_admin: 当前后台用户
    :return: 分页历史清单
    """
    return await _get_single_risk_report_history(db, current_admin, keyword, skip, limit)


@router.get("/risk/single-reports/{report_id}", response_model=CompositeRiskReportResponse)
async def get_single_risk_report_detail(
    report_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """打开历史风控报告。

    :param report_id: 报告ID
    :param db: 异步数据库会话
    :param current_admin: 当前后台用户
    :return: GalaCredit 风险报告
    """
    return await _get_single_risk_report_detail(db, current_admin, report_id)


@router.get("/blacklist")
async def get_blacklist(
    keyword: Optional[str] = Query(None, description="姓名/手机号/身份证号"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_blacklist_entries(db, current_admin, keyword, skip, limit)


@router.post("/blacklist/upload")
async def upload_blacklist(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _upload_blacklist(db, current_admin, file)
    await notify_admin_stats_changed()
    return result


@router.post("/users/{user_id}/blacklist")
async def manual_blacklist_user(
    user_id: int,
    req: LoanFollowUpRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _manual_blacklist_user(db, current_admin, user_id, req)
    await notify_admin_stats_changed()
    return result


@router.post("/users/{user_id}/blacklist/remove")
async def remove_blacklist_user(
    user_id: int,
    req: LoanFollowUpRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _remove_blacklist_user(db, current_admin, user_id, req)
    await notify_admin_stats_changed()
    return result


@router.get("/overdue-fee-configs", response_model=PaginatedOverdueFeeConfigResponse)
async def get_overdue_fee_configs(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_overdue_fee_configs(db, current_admin, skip, limit)


@router.post("/overdue-fee-configs")
async def create_overdue_fee_config(
    req: OverdueFeeConfigCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _create_overdue_fee_config(db, current_admin, req)




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


@router.get("/config-history/{object_type}/{object_id}")
async def get_config_history(object_type: str, object_id: int, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    ensure_any_admin_page_permission(current_admin, ("channels", "products"))
    rows = (await db.execute(select(ConfigChangeHistory).where(ConfigChangeHistory.object_type == object_type.upper(), ConfigChangeHistory.object_id == object_id).order_by(ConfigChangeHistory.version_no.desc()))).scalars().all()
    return {"items": [{"id": x.id, "action": x.action, "version_no": x.version_no, "snapshot": x.snapshot_json, "operator_name": x.operator_name, "created_at": x.created_at} for x in rows]}


@router.get("/exclusive-links", response_model=ExclusiveLinksResponse)
async def get_exclusive_links(
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_exclusive_links(db, current_admin)




@router.post("/channels")
async def create_channel(
    req: ChannelCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _create_channel(db, current_admin, req)
    await notify_admin_stats_changed()
    return result




@router.patch("/channels/{channel_id}")
async def update_channel(
    channel_id: int,
    req: ChannelUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _update_channel(db, current_admin, channel_id, req)
    await notify_admin_stats_changed()
    return result


@router.post("/channels/{channel_id}/copy")
async def copy_channel(channel_id: int, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    ensure_admin_page_permission(current_admin, "channels")
    source = (await db.execute(select(Channel).where(Channel.id == channel_id))).scalar_one_or_none()
    if not source: raise HTTPException(status_code=404, detail="渠道不存在")
    copied = Channel(channel_name=f"{source.channel_name}_COPY_{uuid4().hex[:6]}", invite_code=f"{uuid4().hex[:16]}", sales_name=source.sales_name, status="INACTIVE", disbursement_mode=source.disbursement_mode, review_mode=source.review_mode, note=source.note, admin_user_id=source.admin_user_id)
    db.add(copied); await db.flush(); db.add(ConfigChangeHistory(object_type="CHANNEL", object_id=copied.id, action="COPY", version_no=1, snapshot_json=json.dumps(serialize_channel(copied), default=str, ensure_ascii=False), operator_name=current_admin.username)); await db.commit(); await db.refresh(copied)
    return serialize_channel(copied)


@router.get("/admin-users/business-advisors", response_model=list[BusinessAdvisorItemResponse])
async def get_business_advisors(
    keyword: Optional[str] = Query(None, description="后台用户ID或用户名关键词"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_business_advisors(db, current_admin, keyword, limit)




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


@router.get("/compliance-rules/active")
async def get_active_compliance_rule(
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """查询当前生效的产品合规规则。

    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :return: 当前规则
    """
    ensure_admin_page_permission(current_admin, "products")
    return {"item": serialize_compliance_rule(await get_active_compliance_rule_async(db))}


@router.post("/compliance-rules")
async def create_compliance_rule(
    req: ComplianceRuleCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """创建新的合规规则版本，历史规则保留用于追溯。

    :param req: 合规规则参数
    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :return: 新规则
    """
    ensure_admin_page_permission(current_admin, "products")
    rule = ComplianceRule(
        rule_name=req.rule_name.strip(),
        max_upfront_fee_rate=req.max_upfront_fee_rate,
        max_effective_apr=req.max_effective_apr,
        max_daily_overdue_fee=req.max_daily_overdue_fee,
        min_actual_disbursement_rate=req.min_actual_disbursement_rate,
        max_term_days=req.max_term_days,
        max_installment_count=req.max_installment_count,
        is_active=True,
        effective_at=req.effective_at,
        note=(req.note or "").strip() or None,
        created_by=current_admin.username,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return serialize_compliance_rule(rule)


@router.get("/audit-logs", response_model=PaginatedAdminAuditLogResponse)
async def get_admin_audit_logs(
    keyword: Optional[str] = Query(None, description="姓名、手机号、订单号、备注"),
    actor_type: Optional[str] = Query(None, description="操作者类型"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    object_type: Optional[str] = Query(None, description="对象类型：USER或LOAN"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_admin_audit_logs(db, current_admin, keyword, actor_type, skip, limit, event_type, object_type, start_date, end_date)


@router.get("/audit-logs/export")
async def export_admin_audit_logs(
    keyword: Optional[str] = Query(None), actor_type: Optional[str] = Query(None), event_type: Optional[str] = Query(None),
    object_type: Optional[str] = Query(None), start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async),
):
    """导出审计日志CSV。"""
    payload = await _get_admin_audit_logs(db, current_admin, keyword, actor_type, 0, 10000, event_type, object_type, start_date, end_date)
    lines = ["id,operator,event_type,title,user_phone,loan_order_no,created_at"]
    for item in payload["items"]:
        values = [item.get(key) for key in ("id", "operator_name", "event_type", "title", "user_phone", "loan_order_no", "created_at")]
        lines.append(",".join('"' + str(value or '').replace('"', '""') + '"' for value in values))
    return StreamingResponse(iter(["\ufeff" + "\n".join(lines)]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit-logs.csv"})


@router.get("/kyc-review-queue", response_model=PaginatedKycReviewResponse)
async def get_kyc_review_queue(
    keyword: Optional[str] = Query(None, description="手机号、姓名或身份证号"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_kyc_review_queue(db, current_admin, keyword, skip, limit)


@router.post("/kyc-review/user/{user_id}")
async def review_kyc_user(user_id: int, req: KycReviewActionRequest, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    """处理单个KYC复核结果。"""
    return await _review_kyc_users(db, current_admin, [user_id], req.action, req.note)


@router.post("/kyc-review/batch")
async def batch_review_kyc(req: KycBatchReviewRequest, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    """批量处理KYC复核结果。"""
    return await _review_kyc_users(db, current_admin, req.user_ids, req.action, req.note)


@router.get("/monitoring-summary", response_model=MonitoringSummaryResponse)
async def get_monitoring_summary(
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_monitoring_summary(db, current_admin)


@router.get("/risk-decisions")
async def get_risk_decisions(
    user_id: Optional[int] = Query(None, ge=1),
    loan_id: Optional[int] = Query(None, ge=1),
    stage: Optional[str] = Query(None),
    decision: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """查询风控决策、规则命中和可重放特征快照。"""
    ensure_any_admin_page_permission(current_admin, ("monitoring", "audit-log", "applications", "users"))
    stmt = select(RiskDecision).order_by(RiskDecision.created_at.desc())
    count_stmt = select(func.count(RiskDecision.id))
    filters = []
    if user_id is not None:
        filters.append(RiskDecision.user_id == user_id)
    if loan_id is not None:
        filters.append(RiskDecision.loan_id == loan_id)
    if stage:
        filters.append(RiskDecision.stage == stage.strip().upper())
    if decision:
        filters.append(RiskDecision.decision == decision.strip().upper())
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
    total = int((await db.scalar(count_stmt)) or 0)
    rows = (await db.execute(stmt.offset(skip).limit(limit))).scalars().all()
    decision_ids = [row.decision_id for row in rows]
    hit_map = {}
    if decision_ids:
        hit_rows = (await db.execute(select(RiskRuleHit).where(RiskRuleHit.decision_id.in_(decision_ids)).order_by(RiskRuleHit.id.asc()))).scalars().all()
        for item in hit_rows:
            hit_map.setdefault(item.decision_id, []).append({"rule_code": item.rule_code, "outcome": item.outcome, "severity": item.severity, "detail": item.detail})
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": row.id,
                "decision_id": row.decision_id,
                "user_id": row.user_id,
                "loan_id": row.loan_id,
                "stage": row.stage,
                "decision": row.decision,
                "score": float(row.score) if row.score is not None else None,
                "policy_key": row.policy_key,
                "policy_version": row.policy_version,
                "mode": row.mode,
                "reason_codes": json.loads(row.reason_codes_json or "[]"),
                "feature_snapshot": json.loads(row.feature_snapshot_json or "{}"),
                "rule_hits": hit_map.get(row.decision_id, []),
                "created_at": row.created_at,
            }
            for row in rows
        ],
    }


@router.get("/risk-signals")
async def get_risk_signals(
    user_id: Optional[int] = Query(None, ge=1),
    risk_level: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """查询设备敏感信息授权与风控信号摘要。

    :param user_id: 用户ID
    :param risk_level: 风险等级
    :param skip: 跳过条数
    :param limit: 返回条数
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 设备风险信号分页结果
    """
    ensure_any_admin_page_permission(current_admin, ("risk-strategy", "monitoring", "users"))
    stmt = select(RiskDeviceSignal).order_by(RiskDeviceSignal.created_at.desc())
    count_stmt = select(func.count(RiskDeviceSignal.id))
    filters = []
    if user_id is not None:
        filters.append(RiskDeviceSignal.user_id == user_id)
    if isinstance(risk_level, str) and risk_level.strip():
        filters.append(RiskDeviceSignal.risk_level == risk_level.strip().upper())
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
    total = int((await db.scalar(count_stmt)) or 0)
    rows = (await db.execute(stmt.offset(skip).limit(limit))).scalars().all()
    items = []
    for row in rows:
        try:
            keyword_hits = json.loads(row.keyword_hits_json or "{}")
        except Exception:
            keyword_hits = {}
        try:
            sms_summary = json.loads(row.sms_summary_json or "[]")
        except Exception:
            sms_summary = []
        try:
            app_summary = json.loads(row.app_summary_json or "[]")
        except Exception:
            app_summary = []
        try:
            device_summary = json.loads(row.device_summary_json or "{}")
        except Exception:
            device_summary = {}
        try:
            risk_flags = json.loads(row.risk_flags_json or "{}").get("risk_flags", [])
        except Exception:
            risk_flags = []
        items.append(
            {
                "id": row.id,
                "user_id": row.user_id,
                "consent_granted": bool(row.consent_granted),
                "device_fingerprint": row.device_fingerprint,
                "risk_level": row.risk_level,
                "keyword_hits": keyword_hits,
                "sms_summary": sms_summary,
                "app_summary": app_summary,
                "device_summary": device_summary,
                "risk_flags": risk_flags,
                "payload_json": json.loads(row.payload_json or "{}"),
                "created_at": row.created_at,
            }
        )
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/risk-policies", response_model=RiskPolicyVersionListResponse)
async def get_risk_policies(
    policy_key: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """查询风控策略版本列表。

    :param policy_key: 策略标识
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 策略版本列表
    """
    ensure_any_admin_page_permission(current_admin, ("risk-strategy",))
    rows = await list_risk_policy_versions(db, policy_key=policy_key or None)
    return {"total": len(rows), "items": [serialize_risk_policy_version(row) for row in rows]}


@router.get("/risk-policies/{policy_key}/history", response_model=RiskPolicyVersionListResponse)
async def get_risk_policy_history(
    policy_key: str,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """查询指定策略的版本历史。

    :param policy_key: 策略标识
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 策略版本历史
    """
    ensure_any_admin_page_permission(current_admin, ("risk-strategy",))
    rows = await list_risk_policy_versions(db, policy_key=policy_key)
    return {"total": len(rows), "items": [serialize_risk_policy_version(row) for row in rows]}


@router.post("/risk-policies")
async def create_risk_policy(
    payload: RiskPolicyVersionCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """创建新的风控策略版本。

    :param payload: 创建请求
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 新策略版本
    """
    ensure_any_admin_page_permission(current_admin, ("risk-strategy",))
    row = await create_risk_policy_version(
        db,
        policy_key=payload.policy_key,
        config_json=payload.config_json,
        status=payload.status,
        rollout_percent=payload.rollout_percent,
        created_by=current_admin.username,
    )
    await db.commit()
    await db.refresh(row)
    return serialize_risk_policy_version(row)


@router.patch("/risk-policies/{version_id}")
async def update_risk_policy(
    version_id: int,
    payload: RiskPolicyVersionUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """更新指定风控策略版本。

    :param version_id: 策略版本ID
    :param payload: 更新请求
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 更新后的策略版本
    """
    ensure_any_admin_page_permission(current_admin, ("risk-strategy",))
    row = await update_risk_policy_version(
        db,
        version_id=version_id,
        config_json=payload.config_json,
        status=payload.status,
        rollout_percent=payload.rollout_percent,
    )
    await db.commit()
    await db.refresh(row)
    return serialize_risk_policy_version(row)


@router.post("/risk-policies/{version_id}/copy")
async def copy_risk_policy(
    version_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """复制指定风控策略版本。

    :param version_id: 被复制的策略版本ID
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 新策略版本
    """
    ensure_any_admin_page_permission(current_admin, ("risk-strategy",))
    row = await copy_risk_policy_version(db, version_id=version_id, created_by=current_admin.username)
    await db.commit()
    await db.refresh(row)
    return serialize_risk_policy_version(row)


@router.post("/risk-policies/{version_id}/activate")
async def activate_risk_policy(
    version_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """激活指定风控策略版本。

    :param version_id: 策略版本ID
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 激活后的策略版本
    """
    ensure_any_admin_page_permission(current_admin, ("risk-strategy",))
    row = await activate_risk_policy_version(db, version_id=version_id)
    await db.commit()
    await db.refresh(row)
    return serialize_risk_policy_version(row)


@router.post("/risk-policies/{version_id}/disable")
async def disable_risk_policy(
    version_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """停用指定风控策略版本。

    :param version_id: 策略版本ID
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 停用后的策略版本
    """
    ensure_any_admin_page_permission(current_admin, ("risk-strategy",))
    row = await disable_risk_policy_version(db, version_id=version_id)
    await db.commit()
    await db.refresh(row)
    return serialize_risk_policy_version(row)


@router.post("/risk-decisions/{decision_id}/override")
async def override_risk_decision(
    decision_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """登记风控人工覆盖，不直接修改原始决策记录。

    :param decision_id: 决策流水号
    :param payload: 覆盖动作和原因
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 覆盖记录
    """
    ensure_any_admin_page_permission(current_admin, ("monitoring", "applications", "users"))
    decision = (await db.execute(select(RiskDecision).where(RiskDecision.decision_id == decision_id))).scalar_one_or_none()
    if decision is None:
        raise BizException("Risk decision not found", code=404)
    action = str(payload.get("action") or "").upper()
    reason = str(payload.get("reason") or "").strip()
    if action not in {"APPROVE", "REFER", "DECLINE", "BLOCK"} or not reason:
        raise BizException("Invalid override action or reason", code=400)
    record = RiskManualOverride(decision_id=decision_id, action=action, reason=reason, operator_id=current_admin.id)
    db.add(record)
    await db.flush()
    return {"id": record.id, "decision_id": decision_id, "action": action, "reason": reason}


@router.post("/risk-signals")
async def ingest_risk_signal(
    payload: dict,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """接收已脱敏的设备/IP/速度特征，供 shadow 策略和审计使用。

    :param payload: user_id 及特征字段
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 特征记录摘要
    """
    ensure_any_admin_page_permission(current_admin, ("monitoring", "users"))
    user_id = int(payload.get("user_id") or 0)
    if user_id <= 0:
        raise BizException("user_id is required", code=400)
    record = await record_device_signal(db, user_id=user_id, payload=payload)
    return {"id": record.id, "user_id": record.user_id, "created_at": record.created_at}


@router.get("/monitoring/drilldown/{metric}")
async def monitoring_drilldown(metric: str, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    """查询监控指标对应的订单、用户或任务明细。"""
    ensure_any_admin_page_permission(current_admin, ("monitoring", "users", "applications", "financials"))
    if metric in {"momo_pending", "momo_failed"}:
        status_value = "PENDING" if metric == "momo_pending" else "FAILED"
        rows = (await db.execute(select(MomoTransaction).where(MomoTransaction.status == status_value).order_by(MomoTransaction.created_at.desc()).limit(100))).scalars().all()
        return {"metric": metric, "items": [{"id": x.id, "loan_id": x.loan_id, "amount": float(x.amount or 0), "status": x.status, "created_at": x.created_at} for x in rows]}
    if metric == "kyc_pending":
        rows = (await db.execute(select(User).where(or_(User.real_name_status.is_(None), User.face_auth_status.is_(None))).order_by(User.created_at.desc()).limit(100))).scalars().all()
        return {"metric": metric, "items": [{"id": x.id, "phone": x.phone, "name": x.name, "created_at": x.created_at} for x in rows]}
    return {"metric": metric, "items": []}


@router.get("/message-center", response_model=MessageCenterResponse)
async def get_message_center(
    keyword: Optional[str] = Query(None, description="标题或内容"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    return await _get_message_center(db, current_admin, keyword, skip, limit)


@router.get("/message-templates")
async def get_message_templates(db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    ensure_admin_page_permission(current_admin, "message-center")
    rows = (await db.execute(select(MessageTemplate).order_by(MessageTemplate.template_key, MessageTemplate.version_no.desc()))).scalars().all()
    return {"items": [{"id": x.id, "template_key": x.template_key, "version_no": x.version_no, "title": x.title, "content": x.content, "is_active": x.is_active, "created_at": x.created_at} for x in rows]}


@router.post("/message-templates")
async def save_message_template(payload: dict, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    ensure_admin_page_permission(current_admin, "message-center")
    key = str(payload.get("template_key", "")).strip(); title = str(payload.get("title", "")).strip(); content = str(payload.get("content", "")).strip()
    if not key or not title or not content: raise HTTPException(status_code=400, detail="模板标识、标题和内容不能为空")
    version = int((await db.scalar(select(func.coalesce(func.max(MessageTemplate.version_no), 0)).where(MessageTemplate.template_key == key))) or 0) + 1
    if payload.get("is_active", True): await db.execute(select(MessageTemplate).where(MessageTemplate.template_key == key))
    item = MessageTemplate(template_key=key, version_no=version, title=title, content=content, is_active=bool(payload.get("is_active", True)), created_by=current_admin.username); db.add(item); await db.commit(); await db.refresh(item)
    return {"id": item.id, "version_no": item.version_no, "template_key": item.template_key, "is_active": item.is_active}


@router.patch("/message-templates/{template_id}/active")
async def toggle_message_template(template_id: int, payload: dict, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    ensure_admin_page_permission(current_admin, "message-center"); item = (await db.execute(select(MessageTemplate).where(MessageTemplate.id == template_id))).scalar_one_or_none()
    if not item: raise HTTPException(status_code=404, detail="模板不存在")
    item.is_active = bool(payload.get("is_active")); await db.commit(); return {"id": item.id, "is_active": item.is_active}


@router.get("/momo-transactions")
async def get_momo_transactions(
    loan_id: Optional[int] = Query(None, ge=1),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """查询 MoMo 放款与还款交易流水。

    :param loan_id: 可选贷款订单ID
    :param status: 可选交易状态
    :param skip: 分页偏移
    :param limit: 每页数量
    :param db: 异步数据库会话
    :param current_admin: 当前登录管理员
    :return: MoMo 交易分页结果
    """
    ensure_any_admin_page_permission(current_admin, ("disbursements", "repayments", "financials"))
    stmt = select(MomoTransaction)
    if loan_id:
        stmt = stmt.where(MomoTransaction.loan_id == loan_id)
    if status:
        stmt = stmt.where(MomoTransaction.status == status.strip().upper())
    total = (await db.scalar(select(func.count()).select_from(stmt.subquery()))) or 0
    items = (
        await db.execute(stmt.order_by(MomoTransaction.id.desc()).offset(skip).limit(limit))
    ).scalars().all()
    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [
            {
                "id": item.id,
                "loan_id": item.loan_id,
                "user_id": item.user_id,
                "transaction_type": item.transaction_type,
                "provider": item.provider,
                "provider_reference": item.provider_reference,
                "idempotency_key": item.idempotency_key,
                "phone": item.phone,
                "amount": item.amount,
                "status": item.status,
                "failure_message": item.failure_message,
                "requested_at": item.requested_at,
                "completed_at": item.completed_at,
            }
            for item in items
        ],
    }


@router.get("/finance/reconciliation")
async def get_finance_reconciliation(target_date: Optional[date] = Query(None), db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    """返回指定日期的日汇总、差异单和待对账交易。"""
    ensure_admin_page_permission(current_admin, "financials")
    day = target_date or date.today(); start = datetime.combine(day, datetime.min.time()); end = start + timedelta(days=1)
    transactions = (await db.execute(select(MomoTransaction).where(MomoTransaction.created_at >= start, MomoTransaction.created_at < end).order_by(MomoTransaction.created_at.desc()))).scalars().all()
    pending = [x for x in transactions if x.status == "PENDING"]
    failed = [x for x in transactions if x.status == "FAILED"]
    return {"date": day.isoformat(), "daily_summary": {"transaction_count": len(transactions), "amount": round(sum(float(x.amount or 0) for x in transactions), 2), "success_count": sum(x.status == "SUCCESS" for x in transactions), "failed_count": len(failed)}, "difference_orders": [{"id": x.id, "loan_id": x.loan_id, "status": x.status, "amount": float(x.amount or 0), "provider_reference": x.provider_reference} for x in failed], "pending_reconciliation": [{"id": x.id, "loan_id": x.loan_id, "status": x.status, "amount": float(x.amount or 0), "created_at": x.created_at} for x in pending]}


@router.get("/disbursement-failures")
async def get_disbursement_failures(
    keyword: Optional[str] = Query(None, description="手机号、姓名或身份证号"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    """查询放款失败客户清单。

    :param keyword: 客户筛选词
    :param skip: 分页偏移量
    :param limit: 分页数量
    :param db: 异步数据库会话
    :param current_admin: 当前管理员
    :return: 最近一次失败记录分页结果
    """
    return await _get_disbursement_failures(db, current_admin, keyword, skip, limit)




@router.post("/products")
async def create_product(
    req: ProductCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _create_product(db, current_admin, req)
    await notify_admin_stats_changed()
    return result


@router.post("/products/rights-image")
async def upload_product_rights_image(
    file: UploadFile = File(...),
    current_admin: Admin = Depends(get_current_admin_async),
):
    ensure_admin_page_permission(current_admin, "products")
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    raw = await file.read()
    await file.close()
    if not raw:
        raise HTTPException(status_code=400, detail="图片内容为空")
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过8MB")
    relative_path = save_product_rights_image(raw, content_type=content_type)
    return {"url": build_upload_url(relative_path), "path": relative_path}




@router.patch("/products/{product_id}")
async def update_product(
    product_id: int,
    req: ProductUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _update_product(db, current_admin, product_id, req)
    await notify_admin_stats_changed()
    return result


@router.post("/products/{product_id}/copy")
async def copy_product(product_id: int, db: AsyncSession = Depends(get_async_db), current_admin: Admin = Depends(get_current_admin_async)):
    ensure_admin_page_permission(current_admin, "products")
    source = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not source: raise HTTPException(status_code=404, detail="产品不存在")
    values = {column.name: getattr(source, column.name) for column in Product.__table__.columns if column.name not in {"id", "created_at", "updated_at", "name"}}
    copied = Product(name=f"{source.name}_COPY_{uuid4().hex[:6]}", **values); db.add(copied); await db.flush(); db.add(ConfigChangeHistory(object_type="PRODUCT", object_id=copied.id, action="COPY", version_no=1, snapshot_json=json.dumps(serialize_product(copied), default=str, ensure_ascii=False), operator_name=current_admin.username)); await db.commit(); await db.refresh(copied)
    return serialize_product(copied)




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
    result = await _create_ecard_pool_item(db, current_admin, req)
    await notify_admin_stats_changed()
    return result




@router.post("/ecard-pool/batch-upload")
async def upload_ecard_pool_items(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _upload_ecard_pool_items(db, file,  current_admin)
    await notify_admin_stats_changed()
    return result


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
    result = await _update_ecard_pool_item(db, current_admin, item_id, req)
    await notify_admin_stats_changed()
    return result




@router.post("/loans/{loan_id}/review")
async def review_loan(
    loan_id: int,
    req: LoanReviewRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _review_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




@router.patch("/loans/{loan_id}")
async def update_loan(
    loan_id: int,
    req: LoanUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _update_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




@router.post("/loans/{loan_id}/disburse")
async def disburse_loan(
    loan_id: int,
    req: DisburseRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _disburse_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result


@router.post("/loans/{loan_id}/reject-card")
async def reject_card_loan(
    loan_id: int,
    req: LoanFollowUpRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _reject_card_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result


@router.post("/loans/{loan_id}/reissue-card")
async def reissue_card_loan(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _reissue_card_loan(db, current_admin, loan_id)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result


@router.post("/loans/{loan_id}/close-card-reissue")
async def close_card_reissue(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _close_card_reissue(db, current_admin, loan_id)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result


@router.post("/loans/{loan_id}/extend")
async def extend_loan(
    loan_id: int,
    req: LoanExtensionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _extend_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result


@router.post("/loans/{loan_id}/available-credit/adjust")
async def adjust_available_credit(
    loan_id: int,
    req: AvailableCreditAdjustRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _adjust_available_credit(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result


@router.post("/loans/{loan_id}/approved-credit/set")
async def set_approved_credit_limit(
    loan_id: int,
    req: ApprovedCreditSetRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _set_approved_credit_limit(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result


@router.post("/loans/{loan_id}/overdue-display")
async def update_overdue_display(
    loan_id: int,
    req: OverdueDisplayRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _update_overdue_display(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




@router.post("/loans/{loan_id}/settle")
async def settle_loan(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _settle_loan(db, current_admin, loan_id)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




@router.post("/loans/{loan_id}/finance-reconcile")
async def finance_reconcile_loan(
    loan_id: int,
    req: LoanFinanceReconcileRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _finance_reconcile_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




@router.post("/loans/{loan_id}/remind")
async def remind_loan(
    loan_id: int,
    req: LoanFollowUpRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _remind_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




@router.post("/loans/{loan_id}/collect")
async def collect_loan(
    loan_id: int,
    req: LoanFollowUpRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _collect_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




@router.post("/loans/{loan_id}/ack-repay-attempt", response_model=RepayAttemptAckResponse)
async def ack_repay_attempt(
    loan_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _ack_repay_attempt(db, current_admin, loan_id)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




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
    result = await _assign_loan(db, current_admin, loan_id, req)
    await _notify_user_loan_snapshot_if_needed(db, loan_id)
    await notify_admin_stats_changed()
    return result




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
    result = await _create_admin_user(db, current_admin, req)
    await notify_admin_stats_changed()
    return result




@router.patch("/admin-users/{admin_id}", response_model=AdminUserItemResponse)
async def update_admin_user(
    admin_id: int,
    req: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _update_admin_user(db, current_admin, admin_id, req)
    await notify_admin_stats_changed()
    return result




@router.delete("/admin-users/{admin_id}")
async def delete_admin_user(
    admin_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: Admin = Depends(get_current_admin_async),
):
    result = await _delete_admin_user(db, current_admin, admin_id)
    await notify_admin_stats_changed()
    return result
