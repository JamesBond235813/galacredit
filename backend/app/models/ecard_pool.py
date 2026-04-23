from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.core.database import Base


class EcardPool(Base):
    __tablename__ = "ecard_pool"

    id = Column(Integer, primary_key=True, index=True)
    account = Column(String(100), nullable=False, unique=True, index=True)
    password = Column(String(100), nullable=False)
    face_value = Column(Float, default=0.0, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="AVAILABLE", index=True)
    loan_id = Column(Integer, nullable=True, index=True)
    note = Column(String(255), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
