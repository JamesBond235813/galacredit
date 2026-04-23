from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.services.loan_amounts import normalize_term_days


class LoanBase(BaseModel):
    credit_limit: float = 0.0
    approved_credit_limit: float = 0.0


class LoanCreate(LoanBase):
    pass


class LoanInstallmentItemResponse(BaseModel):
    id: Optional[int] = None
    period_no: int
    due_date: Optional[datetime] = None
    status: str
    principal_amount: float = 0
    interest_amount: float = 0
    guarantee_fee_amount: float = 0
    due_amount: float = 0
    paid_amount: float = 0
    reduction_amount: float = 0
    remaining_amount: float = 0
    paid_principal_amount: float = 0
    paid_interest_amount: float = 0
    paid_guarantee_fee_amount: float = 0
    reduced_principal_amount: float = 0
    reduced_interest_amount: float = 0
    reduced_guarantee_fee_amount: float = 0
    settled_at: Optional[datetime] = None


class LoanFundFlowSummaryResponse(BaseModel):
    installment_periods: int = 0
    expected_principal_amount: float = 0
    expected_interest_amount: float = 0
    expected_guarantee_fee_amount: float = 0
    expected_income_amount: float = 0
    paid_principal_amount: float = 0
    paid_interest_amount: float = 0
    paid_guarantee_fee_amount: float = 0
    paid_penalty_amount: float = 0
    realized_income_amount: float = 0
    reduced_principal_amount: float = 0
    reduced_interest_amount: float = 0
    reduced_guarantee_fee_amount: float = 0
    reduced_penalty_amount: float = 0
    reduced_fee_amount: float = 0
    principal_balance_amount: float = 0
    fee_balance_amount: float = 0
    penalty_amount: float = 0
    penalty_balance_amount: float = 0
    remaining_amount: float = 0
    overdue_installment_count: int = 0
    current_installment_period: Optional[int] = None
    next_due_date: Optional[datetime] = None


class LoanTransactionItemResponse(BaseModel):
    id: int
    transaction_type: str
    transaction_label: str
    amount: float = 0
    principal_amount: float = 0
    interest_amount: float = 0
    guarantee_fee_amount: float = 0
    penalty_amount: float = 0
    operator_name: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


class LoanHistoryResponse(LoanBase):
    id: int
    user_id: int
    status: str
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
    created_at: datetime
    disbursed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoanResponse(LoanBase):
    id: int
    user_id: int
    status: str
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
    reminder_count: int = 0
    last_reminded_at: Optional[datetime] = None
    collection_count: int = 0
    last_collection_at: Optional[datetime] = None
    collection_note: Optional[str] = None
    repay_attempt_count: int = 0
    review_admin_id: Optional[int] = None
    review_admin_name: Optional[str] = None
    collection_admin_id: Optional[int] = None
    collection_admin_name: Optional[str] = None
    collection_transferred_at: Optional[datetime] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    rights_title: Optional[str] = None
    rights_desc: Optional[str] = None
    rights_price: float = 0
    ecard_face_value: float = 0
    product_total_price: float = 0
    product_term_days: Optional[int] = None
    ecard_account_masked: Optional[str] = None
    ecard_password_masked: Optional[str] = None
    ecard_expires_at: Optional[datetime] = None
    has_issued_ecard: bool = False
    relend_count: int = 0
    relend_label: str = "初借"
    latest_settled_loan: Optional[LoanHistoryResponse] = None
    installment_periods: int = 0
    installments: List[LoanInstallmentItemResponse] = Field(default_factory=list)
    fund_flow_summary: Optional[LoanFundFlowSummaryResponse] = None
    created_at: datetime
    disbursed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DisburseRequest(BaseModel):
    term_days: Optional[int] = Field(None, ge=7, le=364)

    @field_validator("term_days")
    @classmethod
    def validate_term_days(cls, value: Optional[int]):
        if value is None:
            return value
        return normalize_term_days(value)


class LoanReviewRequest(BaseModel):
    approved: bool
    credit_limit: Optional[float] = Field(None, ge=0)
    fee_rate: Optional[float] = Field(None, ge=0, le=5)
    term_days: Optional[int] = Field(None, ge=7, le=364)
    review_note: Optional[str] = Field(None, max_length=255)

    @field_validator("term_days")
    @classmethod
    def validate_term_days(cls, value: Optional[int]):
        if value is None:
            return value
        return normalize_term_days(value)


class LoanUpdateRequest(BaseModel):
    credit_limit: Optional[float] = Field(None, ge=0)
    fee_rate: Optional[float] = Field(None, ge=0, le=5)
    term_days: Optional[int] = Field(None, ge=7, le=364)
    due_date: Optional[datetime] = None
    penalty_amount: Optional[float] = Field(None, ge=0)
    review_note: Optional[str] = Field(None, max_length=255)
    collection_note: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None

    @field_validator("term_days")
    @classmethod
    def validate_term_days(cls, value: Optional[int]):
        if value is None:
            return value
        return normalize_term_days(value)


class LoanFollowUpRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=255)


class LoanAssignRequest(BaseModel):
    stage: str = Field(..., description="review | collection")
    admin_id: int = Field(..., ge=1)


class LoanAssigneeItemResponse(BaseModel):
    id: int
    username: str


class LoanAssignmentResponse(BaseModel):
    loan_id: int
    stage: str
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None


class LoanFinanceReconcileRequest(BaseModel):
    received_amount: float = Field(0, ge=0)
    reduction_amount: float = Field(0, ge=0)
    note: Optional[str] = Field(None, max_length=255)


class LoanWithUserResponse(LoanResponse):
    user_phone: str
    user_name: Optional[str] = None
    user_id_card_num: Optional[str] = None
    user_face_auth_status: Optional[str] = None
    user_source_channel_name: Optional[str] = None
    user_source_channel_sales_name: Optional[str] = None
    application_submitted_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedLoanResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[LoanWithUserResponse]


class LoanLedgerResponse(BaseModel):
    loan_id: int
    loan_status: str
    installments: List[LoanInstallmentItemResponse] = Field(default_factory=list)
    transactions: List[LoanTransactionItemResponse] = Field(default_factory=list)
    fund_flow_summary: LoanFundFlowSummaryResponse


class RepaymentStatsResponse(BaseModel):
    receivable_user_count: int
    receivable_amount: float
    received_user_count: int
    received_amount: float
    repayment_rate: float
    repeat_borrow_count: int
    repeat_borrow_rate: float
    reduction_amount: float
    disbursed_amount: float = 0
    expected_interest_amount: float = 0
    expected_guarantee_fee_amount: float = 0
    expected_income_amount: float = 0
    realized_income_amount: float = 0
    outstanding_principal_amount: float = 0
    overdue_outstanding_amount: float = 0
    reduced_principal_amount: float = 0
    reduced_fee_amount: float = 0


class AdminStatsResponse(BaseModel):
    total_users: int
    today_new_users: int
    today_applications: int
    reviewing_loans: int
    approved_loans: int
    withdrawing_loans: int
    disbursed_loans: int
    due_today_loans: int
    due_today_users: int = 0
    repay_attempt_total: int = 0
    overdue_loans: int
    today_disbursed_amount: float
    today_reminders: int
    today_collections: int


class RepayAttemptAckResponse(BaseModel):
    loan_id: int
    cleared_count: int = 0
    repay_attempt_count: int = 0


class ProjectCashInsightLineResponse(BaseModel):
    key: str
    label: str
    payment_amount: float = 0
    receipt_amount: float = 0
    net_amount: float = 0


class ProjectCashInsightItemResponse(BaseModel):
    project_key: str
    project_name: str
    project_subtitle: Optional[str] = None
    borrower_count: int = 0
    loan_count: int = 0
    active_loan_count: int = 0
    overdue_loan_count: int = 0
    settled_loan_count: int = 0
    total_payment_amount: float = 0
    total_receipt_amount: float = 0
    total_net_amount: float = 0
    line_items: List[ProjectCashInsightLineResponse] = Field(default_factory=list)


class ProjectCashInsightResponse(BaseModel):
    class InsightMetricCardResponse(BaseModel):
        key: str
        title: str
        value: float = 0
        value_type: str = "currency"  # currency | count
        sub_label: str = "今日"
        sub_value: float = 0

    total_projects: int = 0
    total_borrowers: int = 0
    total_loans: int = 0
    total_payment_amount: float = 0
    total_receipt_amount: float = 0
    total_net_amount: float = 0
    notes: List[str] = Field(default_factory=list)
    cards: List[InsightMetricCardResponse] = Field(default_factory=list)
    items: List[ProjectCashInsightItemResponse] = Field(default_factory=list)


class ProductItemResponse(BaseModel):
    id: int
    name: str
    ecard_face_value: float = 0
    rights_price: float = 0
    rights_title: str
    rights_desc: Optional[str] = None
    term_days: int
    payment_amount: float = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    ecard_face_value: float = Field(..., gt=0)
    rights_price: float = Field(..., ge=0)
    rights_title: str = Field(..., min_length=1, max_length=120)
    rights_desc: Optional[str] = Field(None, max_length=1000)
    term_days: int = Field(..., ge=7, le=364)
    payment_amount: Optional[float] = Field(None, gt=0)
    is_active: bool = True

    @field_validator("term_days")
    @classmethod
    def validate_term_days_for_product(cls, value: Optional[int]):
        if value is None:
            return value
        return normalize_term_days(value)


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    ecard_face_value: Optional[float] = Field(None, gt=0)
    rights_price: Optional[float] = Field(None, ge=0)
    rights_title: Optional[str] = Field(None, min_length=1, max_length=120)
    rights_desc: Optional[str] = Field(None, max_length=1000)
    term_days: Optional[int] = Field(None, ge=7, le=364)
    payment_amount: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None

    @field_validator("term_days")
    @classmethod
    def validate_term_days_for_product(cls, value: Optional[int]):
        if value is None:
            return value
        return normalize_term_days(value)


class PaginatedProductResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[ProductItemResponse]


class LoanOrderRequest(BaseModel):
    product_id: int = Field(..., ge=1)


class EcardPoolItemResponse(BaseModel):
    id: int
    account: str
    password: str
    face_value: float
    expires_at: datetime
    status: str
    loan_id: Optional[int] = None
    note: Optional[str] = None
    assigned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class EcardPoolCreateRequest(BaseModel):
    account: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)
    face_value: float = Field(..., gt=0)
    expires_at: datetime
    note: Optional[str] = Field(None, max_length=255)


class EcardPoolUpdateRequest(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None


class PaginatedEcardPoolResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[EcardPoolItemResponse]


class EcardSecretResponse(BaseModel):
    field: str
    value: str
