from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.services.channel_service import normalize_channel_name, normalize_channel_status


class ChannelLandingResponse(BaseModel):
    id: int
    channel_name: str
    sales_name: str
    status: str


class ChannelCreateRequest(BaseModel):
    channel_name: str = Field(..., min_length=2, max_length=32)
    invite_code: Optional[str] = Field(None, min_length=16, max_length=32)
    sales_name: str = Field(..., min_length=1, max_length=50)
    status: Optional[str] = Field("ACTIVE", max_length=20)
    note: Optional[str] = Field(None, max_length=255)
    admin_user_id: int = Field(..., ge=1)

    @field_validator("channel_name")
    @classmethod
    def validate_channel_name(cls, value: str):
        return normalize_channel_name(value)

    @field_validator("invite_code")
    @classmethod
    def validate_invite_code(cls, value: Optional[str]):
        if value is None:
            return value
        normalized = (value or "").strip().lower()
        if len(normalized) < 16 or len(normalized) > 32:
            raise ValueError("渠道邀请码长度必须为 16-32 位")
        if not normalized.isalnum():
            raise ValueError("渠道邀请码仅支持小写字母和数字")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]):
        return normalize_channel_status(value)


class ChannelUpdateRequest(BaseModel):
    sales_name: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = Field(None, max_length=255)
    admin_user_id: Optional[int] = Field(None, ge=1)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]):
        if value is None:
            return value
        return normalize_channel_status(value)


class ChannelBindRequest(BaseModel):
    channel_name: str = Field(..., min_length=2, max_length=32)

    @field_validator("channel_name")
    @classmethod
    def validate_channel_name(cls, value: str):
        return normalize_channel_name(value)


class ChannelBindResponse(BaseModel):
    msg: str
    source_channel_name: Optional[str] = None
    source_channel_sales_name: Optional[str] = None


class ChannelItemResponse(BaseModel):
    id: int
    channel_name: str
    invite_code: str
    sales_name: str
    status: str
    note: Optional[str] = None
    admin_user_id: Optional[int] = None
    admin_user_name: Optional[str] = None
    created_at: datetime
    attributed_user_count: int = 0
    submitted_user_count: int = 0
    application_count: int = 0
    disbursed_user_count: int = 0
    disbursed_amount: float = 0
    overdue_user_count: int = 0
    overdue_amount: float = 0
    overdue_rate: float = 0
    latest_application_at: Optional[datetime] = None
    latest_disbursed_at: Optional[datetime] = None


class ChannelSummaryResponse(BaseModel):
    total_channels: int = 0
    active_channels: int = 0
    inactive_channels: int = 0
    attributed_user_count: int = 0
    submitted_user_count: int = 0
    application_count: int = 0
    disbursed_user_count: int = 0
    disbursed_amount: float = 0
    overdue_user_count: int = 0
    overdue_amount: float = 0
    overdue_rate: float = 0


class PaginatedChannelResponse(BaseModel):
    total: int
    page: int
    size: int
    channel_link_prefix: str
    summary: ChannelSummaryResponse
    items: List[ChannelItemResponse]


class BusinessAdvisorItemResponse(BaseModel):
    id: int
    username: str
