from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class UserPhoneBinding(Base):
    __tablename__ = "user_phone_bindings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    bind_type = Column(String(30), nullable=False, default="ACTIVE")
    note = Column(String(255), nullable=True)
    bound_at = Column(DateTime, nullable=False, default=datetime.now)
    unbound_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
