from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from app.schemas.loan import LoanFundFlowSummaryResponse, LoanHistoryResponse, LoanInstallmentItemResponse


class UserBase(BaseModel):
    phone: str


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    id_card_num: Optional[str] = None
    id_address: Optional[str] = None
    id_expiry: Optional[str] = None
    approved_limit: Optional[int] = None


class UserResponse(UserBase):
    id: int
    name: Optional[str] = None
    id_card_num: Optional[str] = None
    id_address: Optional[str] = None
    id_expiry: Optional[str] = None
    approved_limit: Optional[int] = None
    emergency_contact1_name: Optional[str] = None
    emergency_contact1_relation: Optional[str] = None
    emergency_contact1_phone: Optional[str] = None
    emergency_contact2_name: Optional[str] = None
    emergency_contact2_relation: Optional[str] = None
    emergency_contact2_phone: Optional[str] = None
    location_latitude: Optional[str] = None
    location_longitude: Optional[str] = None
    location_accuracy: Optional[str] = None
    location_address: Optional[str] = None
    location_province: Optional[str] = None
    location_city: Optional[str] = None
    location_district: Optional[str] = None
    location_street: Optional[str] = None
    location_source: Optional[str] = None
    location_updated_at: Optional[datetime] = None
    face_auth_status: Optional[str] = None
    real_name_status: Optional[str] = None
    face_auth_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    ocr_submitted_at: Optional[datetime] = None
    application_submitted_at: Optional[datetime] = None
    source_channel_name: Optional[str] = None
    source_channel_sales_name: Optional[str] = None
    channel_bound_at: Optional[datetime] = None
    last_channel_visit_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime


class SendCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\d{11}$")


class LoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\d{11}$")
    password: str = Field(..., min_length=6, max_length=50)
    channel_name: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=50)
    new_password: str = Field(..., min_length=6, max_length=50)
    confirm_password: str = Field(..., min_length=6, max_length=50)


class EmergencyContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    relation: str = Field(..., min_length=1, max_length=20)
    phone: str = Field(..., pattern=r"^\d{11}$")


class ApplicationSubmitRequest(BaseModel):
    emergency_contacts: List[EmergencyContactRequest] = Field(..., min_length=2, max_length=2)


class UserLocationUpsertRequest(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    source: Optional[str] = Field(default="h5-geolocation", max_length=30)


class UserEventResponse(BaseModel):
    id: int
    loan_id: Optional[int] = None
    actor_type: str
    operator_name: Optional[str] = None
    event_type: str
    title: str
    detail: Optional[str] = None
    created_at: datetime


class UserLoanSnapshotResponse(BaseModel):
    id: int
    status: str
    credit_limit: float
    fee_rate: float = 0.6
    fee_amount: float = 0
    interest_amount: float = 0
    guarantee_fee_amount: float = 0
    installment_amount: float = 0
    term_days: Optional[int] = None
    due_date: Optional[datetime] = None
    penalty_amount: float
    repaid_amount: float = 0
    reduction_amount: float = 0
    total_repayment_amount: float = 0
    remaining_repayment_amount: float = 0
    review_note: Optional[str] = None
    approved_at: Optional[datetime] = None
    reminder_count: int
    last_reminded_at: Optional[datetime] = None
    collection_count: int
    last_collection_at: Optional[datetime] = None
    collection_note: Optional[str] = None
    relend_count: int = 0
    relend_label: str = "初借"
    latest_settled_loan: Optional[LoanHistoryResponse] = None
    installment_periods: int = 0
    installments: List[LoanInstallmentItemResponse] = Field(default_factory=list)
    fund_flow_summary: Optional[LoanFundFlowSummaryResponse] = None
    created_at: datetime
    disbursed_at: Optional[datetime] = None


class UserListItemResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str] = None
    id_card_num: Optional[str] = None
    face_auth_status: Optional[str] = None
    real_name_status: Optional[str] = None
    approved_limit: Optional[int] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None
    application_submitted_at: Optional[datetime] = None
    current_loan_id: Optional[int] = None
    current_loan_status: Optional[str] = None
    current_credit_limit: Optional[float] = None
    current_term_days: Optional[int] = None
    current_due_date: Optional[datetime] = None
    current_fee_rate: Optional[float] = None
    current_fee_amount: Optional[float] = None
    current_interest_amount: Optional[float] = None
    current_guarantee_fee_amount: Optional[float] = None
    current_penalty_amount: Optional[float] = None
    first_disbursed_at: Optional[datetime] = None
    first_deal_amount: Optional[float] = None
    latest_disbursed_at: Optional[datetime] = None
    latest_deal_amount: Optional[float] = None
    source_channel_name: Optional[str] = None
    source_channel_sales_name: Optional[str] = None
    channel_bound_at: Optional[datetime] = None
    last_channel_visit_at: Optional[datetime] = None


class PaginatedUserResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[UserListItemResponse]


class UserDetailResponse(UserResponse):
    latest_loan: Optional[UserLoanSnapshotResponse] = None
    first_deal_loan: Optional[UserLoanSnapshotResponse] = None
    events: List[UserEventResponse] = Field(default_factory=list)
