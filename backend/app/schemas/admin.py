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
