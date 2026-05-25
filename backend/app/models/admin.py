from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.core.database import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    roles = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)
    active_session_id = Column(String(64), nullable=True, index=True)
    active_session_issued_at = Column(DateTime, nullable=True)
    active_web_session_id = Column(String(64), nullable=True, index=True)
    active_web_session_issued_at = Column(DateTime, nullable=True)
    active_mobile_session_id = Column(String(64), nullable=True, index=True)
    active_mobile_session_issued_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
