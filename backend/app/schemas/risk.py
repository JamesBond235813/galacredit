from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AdminRiskReportRequest(BaseModel):
    user_id: int = Field(..., ge=1)


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
    name: str
    id_card: str
    phone: str
    report_json: Any
    query_time: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
