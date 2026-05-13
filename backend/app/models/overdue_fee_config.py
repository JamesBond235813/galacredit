from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, Integer, String

from app.core.database import Base


class OverdueFeeConfig(Base):
    __tablename__ = "overdue_fee_configs"

    id = Column(Integer, primary_key=True, index=True)
    daily_penalty_amount = Column(Float, default=10.0, nullable=False)
    effective_date = Column(Date, nullable=False, index=True)
    note = Column(String(255), nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
