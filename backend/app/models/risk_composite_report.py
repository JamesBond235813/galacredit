from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class RiskCompositeReport(Base):
    __tablename__ = "risk_composite_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    panorama_report_id = Column(Integer, nullable=True, index=True)
    probe_a_report_id = Column(Integer, nullable=True, index=True)
    name = Column(String(255), nullable=True, index=True)
    id_card = Column(String(255), nullable=True, index=True)
    phone = Column(String(255), nullable=True, index=True)
    report_json = Column(Text, nullable=True)
    query_time = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
