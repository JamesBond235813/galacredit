from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from app.schemas.loan import LoanFundFlowSummaryResponse, LoanHistoryResponse, LoanInstallmentItemResponse

FAMILY_CONTACT_RELATIONS = ("Parents", "Brothers or sisters", "Grandparents", "Couple", "Children")
SOCIAL_CONTACT_RELATIONS = ("Friends", "Classmates", "Colleagues")
AUTH_PHONE_PATTERN = r"^(?:\d{11}|233\d{9})$"


class UserBase(BaseModel):
    phone: str


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    id_card_num: Optional[str] = None
    id_address: Optional[str] = None
    id_expiry: Optional[str] = None
    id_card_front_image_url: Optional[str] = None
    id_card_back_image_url: Optional[str] = None
    face_image_url: Optional[str] = None
    approved_limit: Optional[int] = None
    available_credit_limit: float = 0
    overdue_credit_locked: bool = False
    blacklist_hit: bool = False
    blacklist_reason: Optional[str] = None
    blacklist_checked_at: Optional[datetime] = None
    risk_list_hit: bool = False
    risk_list_source: Optional[str] = None
    risk_list_reason: Optional[str] = None
    risk_list_checked_at: Optional[datetime] = None


class UserResponse(UserBase):
    id: int
    name: Optional[str] = None
    id_card_num: Optional[str] = None
    id_address: Optional[str] = None
    id_expiry: Optional[str] = None
    id_card_front_image_url: Optional[str] = None
    id_card_back_image_url: Optional[str] = None
    face_image_url: Optional[str] = None
    approved_limit: Optional[int] = None
    available_credit_limit: float = 0
    overdue_credit_locked: bool = False
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
    location_risk_blocked: bool = False
    location_risk_reason: Optional[str] = None
    location_risk_at: Optional[datetime] = None
    risk_list_hit: bool = False
    risk_list_source: Optional[str] = None
    risk_list_reason: Optional[str] = None
    risk_list_checked_at: Optional[datetime] = None
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
    phone_reclaimed: bool = False
    previous_user_id: Optional[int] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    access_token_expires_at: Optional[datetime] = None
    refresh_token_expires_at: Optional[datetime] = None
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
    phone: str = Field(..., pattern=AUTH_PHONE_PATTERN)
    captcha_ticket: str = Field(..., min_length=10, max_length=128)


class LoginRequest(BaseModel):
    phone: str = Field(..., pattern=AUTH_PHONE_PATTERN)
    password: str = Field(..., min_length=6, max_length=50)
    channel_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None


class SmsLoginRequest(BaseModel):
    phone: str = Field(..., pattern=AUTH_PHONE_PATTERN)
    sms_code: str = Field(..., pattern=r"^\d{6}$")
    invite_code: Optional[str] = Field(None, pattern=r"^[a-z0-9]{24,32}$")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    device_signal_id: Optional[int] = Field(None, ge=1)


class RiskDeviceSmsItem(BaseModel):
    """短信摘要项。"""

    sender: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)


class RiskDeviceAppItem(BaseModel):
    """应用摘要项。"""

    name: Optional[str] = None
    package: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)


class RiskDeviceClientPayload(BaseModel):
    """设备授权采集载荷。"""

    consent_sms: bool = False
    consent_app_list: bool = False
    consent_device_fingerprint: bool = True
    sms_messages: list[dict[str, Any]] = Field(default_factory=list)
    installed_apps: list[dict[str, Any]] = Field(default_factory=list)
    device_profile: dict[str, Any] = Field(default_factory=dict)
    native_bridge: Optional[str] = None
    source: Optional[str] = Field(default="H5", max_length=30)
    app_channel: Optional[str] = Field(default="play", max_length=20)
    app_version: Optional[str] = Field(default=None, max_length=40)
    platform: Optional[str] = Field(default=None, max_length=40)
    browser_name: Optional[str] = Field(default=None, max_length=40)
    browser_version: Optional[str] = Field(default=None, max_length=40)
    screen_width: Optional[int] = Field(None, ge=0)
    screen_height: Optional[int] = Field(None, ge=0)
    timezone: Optional[str] = Field(default=None, max_length=64)
    language: Optional[str] = Field(default=None, max_length=20)
    device_fingerprint: Optional[str] = Field(default=None, max_length=128)
    consent_version: Optional[str] = Field(default="2026-08", max_length=20)
    sms_keywords: list[str] = Field(default_factory=list)
    app_keywords: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


class RiskDeviceSignalResponse(BaseModel):
    """设备风险信号记录。"""

    id: int
    user_id: int
    consent_granted: bool
    device_fingerprint: Optional[str] = None
    risk_level: str
    keyword_hits: dict[str, list[str]]
    sms_summary: list[RiskDeviceSmsItem]
    app_summary: list[RiskDeviceAppItem]
    device_summary: dict[str, Any]
    risk_flags: list[str]
    payload_json: dict[str, Any]
    created_at: datetime


class RiskDeviceSignalListResponse(BaseModel):
    """设备风险信号分页列表。"""

    total: int
    skip: int
    limit: int
    items: list[RiskDeviceSignalResponse]


class RiskDeviceConsentRequest(BaseModel):
    """设备风险授权请求。"""

    phone: str = Field(..., pattern=AUTH_PHONE_PATTERN)
    accepted_user_agreement: bool = False
    accepted_personal_authorization: bool = False
    accepted_sensitive_collection: bool = False
    device_payload: RiskDeviceClientPayload = Field(default_factory=RiskDeviceClientPayload)


class RiskDeviceConsentResponse(BaseModel):
    """设备风险授权结果。"""

    consent_id: int
    signal_id: int
    device_fingerprint: Optional[str] = None
    risk_level: str
    keyword_hits: dict[str, list[str]]
    risk_flags: list[str]
    task_number: Optional[str] = None
    message: str


class RiskTaskQueryRequest(BaseModel):
    """第三方 Ghana 风控任务查询请求。"""

    task_number: str = Field(..., min_length=8, max_length=64)


class RiskTaskQueryResponse(BaseModel):
    """第三方 Ghana 风控任务查询结果。"""

    task_number: str
    task_status: Optional[str] = None
    task_score: Optional[float] = None
    message: str


class SliderCaptchaCreateRequest(BaseModel):
    phone: str = Field(..., pattern=AUTH_PHONE_PATTERN)
    width: int = Field(..., ge=1, le=2000)


class SliderCaptchaCreateResponse(BaseModel):
    captcha_id: str
    width: int
    height: int
    block_size: int
    block_y: int
    background_image: str
    slider_image: str
    min_elapsed_ms: int


class SliderCaptchaVerifyRequest(BaseModel):
    phone: str = Field(..., pattern=AUTH_PHONE_PATTERN)
    captcha_id: str = Field(..., min_length=8, max_length=128)
    offset_x: float = Field(...)
    elapsed_ms: int = Field(..., ge=0, le=60000)


class SliderCaptchaVerifyResponse(BaseModel):
    captcha_ticket: str
    expires_seconds: int


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
    phone: str = Field(..., pattern=r"^(?:233\d{9}|\d{11})$")
    source: Literal["CONTACT_PICKER"] = Field(..., description="联系人必须来自设备通讯录选择器")
    category: Literal["FAMILY", "SOCIAL"]

    @field_validator("relation", mode="before")
    @classmethod
    def normalize_relation(cls, value: str):
        """规范化联系人关系文本。

        :param value: 联系人关系
        :return: 去除前后空格后的联系人关系
        """
        if isinstance(value, str):
            return value.strip()
        return value


class ApplicationSubmitRequest(BaseModel):
    emergency_contacts: List[EmergencyContactRequest] = Field(..., min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_contact_categories(self):
        """校验两位紧急联系人的类别和关系。

        :return: 校验通过的申请请求
        """
        family_contact, social_contact = self.emergency_contacts
        if family_contact.category != "FAMILY" or family_contact.relation not in FAMILY_CONTACT_RELATIONS:
            raise ValueError("Emergency contact 1 must be a family member")
        if social_contact.category != "SOCIAL" or social_contact.relation not in SOCIAL_CONTACT_RELATIONS:
            raise ValueError("Emergency contact 2 must be a friend, classmate, or colleague")
        return self


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
    ip: str = ""
    ip_country: str = ""
    ip_province: str = ""
    ip_city: str = ""
    ip_district: str = ""
    ip_detail: str = ""
    lon_lat: str = ""
    lon_lat_province: str = ""
    lon_lat_city: str = ""
    lon_lat_district: str = ""
    lon_lat_detail: str = ""
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
    risk_report_checked_at: Optional[datetime] = None
    risk_report_checked_by: Optional[str] = None
    approval_discount_amount: float = 0
    order_discount_amount: float = 0
    card_reissue_closed: bool = False
    extension_count: int = 0
    extension_type: Optional[str] = None
    extension_note: Optional[str] = None
    overdue_hidden: bool = False
    available_credit_limit: float = 0
    overdue_credit_locked: bool = False
    extension_source_loan_id: Optional[int] = None
    extension_used_at: Optional[datetime] = None
    is_extension_fee_order: bool = False
    fee_extension_ready: bool = False
    relend_count: int = 0
    relend_label: str = "首购"
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
    id_card_front_image_url: Optional[str] = None
    id_card_back_image_url: Optional[str] = None
    face_image_url: Optional[str] = None
    face_auth_status: Optional[str] = None
    real_name_status: Optional[str] = None
    approved_limit: Optional[int] = None
    available_credit_limit: float = 0
    overdue_credit_locked: bool = False
    blacklist_hit: bool = False
    blacklist_reason: Optional[str] = None
    blacklist_checked_at: Optional[datetime] = None
    location_risk_blocked: bool = False
    location_risk_reason: Optional[str] = None
    location_risk_at: Optional[datetime] = None
    risk_list_hit: bool = False
    risk_list_source: Optional[str] = None
    risk_list_reason: Optional[str] = None
    risk_list_checked_at: Optional[datetime] = None
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
    current_blacklist_hit: bool = False
    first_disbursed_at: Optional[datetime] = None
    first_deal_amount: Optional[float] = None
    latest_disbursed_at: Optional[datetime] = None
    latest_deal_amount: Optional[float] = None
    source_channel_name: Optional[str] = None
    source_channel_sales_name: Optional[str] = None
    channel_bound_at: Optional[datetime] = None
    last_channel_visit_at: Optional[datetime] = None
    can_unlock_location_risk: bool = False


class PaginatedUserResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[UserListItemResponse]


class UserDetailResponse(UserResponse):
    latest_loan: Optional[UserLoanSnapshotResponse] = None
    first_deal_loan: Optional[UserLoanSnapshotResponse] = None
    can_unlock_location_risk: bool = False
    events: List[UserEventResponse] = Field(default_factory=list)
