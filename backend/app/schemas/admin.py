from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class AdminCreate(AdminBase):
    password: str


class AdminResponse(AdminBase):
    id: int
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class AdminLogin(BaseModel):
    username: str
    password: str
    client_type: Optional[str] = Field(default="WEB")


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str


class AdminUserCreateRequest(AdminBase):
    password: str = Field(..., min_length=6, max_length=50)
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)


class AdminUserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=50)
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AdminUserItemResponse(AdminResponse):
    is_current: bool = False


class PaginatedAdminUserResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[AdminUserItemResponse]


class RegisterUserRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\d{11}$")
    password: str = Field(..., min_length=6, max_length=50)
    source_channel_id: Optional[int] = None


class ResetUserPasswordRequest(BaseModel):
    password: str = Field(..., min_length=6, max_length=50)


class AdminChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=50)
    new_password: str = Field(..., min_length=6, max_length=50)
    confirm_password: str = Field(..., min_length=6, max_length=50)


class ComplianceRuleCreateRequest(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100)
    max_upfront_fee_rate: Optional[float] = Field(None, ge=0, le=1)
    max_effective_apr: Optional[float] = Field(None, ge=0)
    max_daily_overdue_fee: Optional[float] = Field(None, ge=0)
    min_actual_disbursement_rate: Optional[float] = Field(None, ge=0, le=1)
    max_term_days: Optional[int] = Field(None, ge=1, le=3650)
    max_installment_count: Optional[int] = Field(None, ge=1, le=120)
    effective_at: datetime
    note: Optional[str] = Field(None, max_length=255)


class AdminAuditLogItemResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    loan_id: Optional[int] = None
    loan_order_no: Optional[str] = None
    actor_type: str
    operator_name: Optional[str] = None
    event_type: str
    title: str
    detail: Optional[str] = None
    created_at: datetime


class PaginatedAdminAuditLogResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[AdminAuditLogItemResponse]


class KycReviewItemResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str] = None
    id_card_num: Optional[str] = None
    face_auth_status: Optional[str] = None
    real_name_status: Optional[str] = None
    application_submitted_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    source_channel_name: Optional[str] = None
    source_channel_sales_name: Optional[str] = None
    review_flags: List[str] = Field(default_factory=list)
    suggested_action: str
    created_at: datetime


class PaginatedKycReviewResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[KycReviewItemResponse]


class KycReviewActionRequest(BaseModel):
    """KYC审核动作请求。"""

    action: str = Field(..., pattern=r"^(APPROVE|REJECT)$")
    note: Optional[str] = Field(None, max_length=500)


class KycBatchReviewRequest(BaseModel):
    """KYC批量审核请求。"""

    user_ids: List[int] = Field(..., min_length=1, max_length=100)
    action: str = Field(..., pattern=r"^(APPROVE|REJECT)$")
    note: Optional[str] = Field(None, max_length=500)


class MonitoringJobResponse(BaseModel):
    job_id: str
    next_run_time: Optional[datetime] = None
    trigger: Optional[str] = None
    pending: bool = False


class MonitoringSummaryResponse(BaseModel):
    admin_event_count_24h: int = 0
    kyc_pending_count: int = 0
    reminder_event_count_24h: int = 0
    collection_event_count_24h: int = 0
    momo_pending_count: int = 0
    momo_failed_count: int = 0
    active_compliance_rule_count: int = 0
    overdue_loan_count: int = 0
    scheduled_jobs: List[MonitoringJobResponse] = Field(default_factory=list)


class MessageTemplateItemResponse(BaseModel):
    key: str
    title: str
    channel: str
    trigger: str
    body: str
    enabled: bool = True


class MessageLogItemResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    loan_id: Optional[int] = None
    actor_type: str
    title: str
    detail: Optional[str] = None
    created_at: datetime


class MessageCenterResponse(BaseModel):
    summary: dict
    templates: List[MessageTemplateItemResponse] = Field(default_factory=list)
    recent_logs: List[MessageLogItemResponse] = Field(default_factory=list)
    reminder_queue: List[dict] = Field(default_factory=list)
