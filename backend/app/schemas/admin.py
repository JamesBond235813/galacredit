from datetime import datetime
from typing import List, Optional

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
    effective_at: datetime
    note: Optional[str] = Field(None, max_length=255)
