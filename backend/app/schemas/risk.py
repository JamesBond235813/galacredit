from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class AdminRiskReportRequest(BaseModel):
    user_id: int = Field(..., ge=1)


class AdminRiskSingleReportRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    id_card: Optional[str] = Field(None, max_length=30)
    phone: Optional[str] = Field(None, max_length=20)


class RiskReportResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    id_card: str
    phone: str
    source: Optional[str] = None
    report_json: Any
    query_time: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompositeRiskReportResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    panorama_report_id: Optional[int] = None
    probe_a_report_id: Optional[int] = None
    probe_c_report_id: Optional[int] = None
    name: Optional[str] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    report_json: Any
    query_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskSingleReportHistoryItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: Optional[str] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    query_time: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedRiskSingleReportHistoryResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[RiskSingleReportHistoryItem]
