from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class RiskControlReport(Base):
    __tablename__ = "risk_control_report"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True, index=True)
    id_card = Column(String(255), nullable=True, index=True)
    phone = Column(String(255), nullable=True, index=True)
    source = Column(String(20), nullable=True, index=True)
    report_json = Column(Text, nullable=True)
    query_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
