from sqlalchemy import Boolean, Column, Float, Integer, String, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(50), nullable=True)
    id_card_num = Column(String(30), nullable=True, unique=True)
    id_address = Column(String(200), nullable=True)
    id_expiry = Column(String(50), nullable=True)
    id_card_front_image = Column(String(255), nullable=True)
    id_card_back_image = Column(String(255), nullable=True)
    face_image = Column(String(255), nullable=True)
    emergency_contact1_name = Column(String(50), nullable=True)
    emergency_contact1_relation = Column(String(20), nullable=True)
    emergency_contact1_phone = Column(String(20), nullable=True)
    emergency_contact2_name = Column(String(50), nullable=True)
    emergency_contact2_relation = Column(String(20), nullable=True)
    emergency_contact2_phone = Column(String(20), nullable=True)
    location_latitude = Column(String(32), nullable=True)
    location_longitude = Column(String(32), nullable=True)
    location_accuracy = Column(String(32), nullable=True)
    location_address = Column(String(255), nullable=True)
    location_province = Column(String(50), nullable=True)
    location_city = Column(String(50), nullable=True)
    location_district = Column(String(50), nullable=True)
    location_street = Column(String(80), nullable=True)
    location_source = Column(String(30), nullable=True)
    location_updated_at = Column(DateTime, nullable=True)
    location_risk_blocked = Column(Boolean, default=False, nullable=False)
    location_risk_reason = Column(String(255), nullable=True)
    location_risk_at = Column(DateTime, nullable=True)
    face_auth_status = Column(String(20), default="PENDING")
    real_name_status = Column(String(20), default="UNVERIFIED")
    face_auth_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    ocr_submitted_at = Column(DateTime, nullable=True)
    application_submitted_at = Column(DateTime, nullable=True)
    source_channel_id = Column(Integer, nullable=True, index=True)
    channel_bound_at = Column(DateTime, nullable=True)
    last_channel_visit_at = Column(DateTime, nullable=True)
    blacklist_hit = Column(Boolean, default=False, nullable=False, index=True)
    blacklist_reason = Column(String(255), nullable=True)
    blacklist_checked_at = Column(DateTime, nullable=True)
    risk_list_hit = Column(Boolean, default=False, nullable=False, index=True)
    risk_list_source = Column(String(50), nullable=True)
    risk_list_reason = Column(String(255), nullable=True)
    risk_list_checked_at = Column(DateTime, nullable=True)
    
    # 模拟授信额度保存 (在获取到审核后写入)
    approved_limit = Column(Integer, default=0)
    available_credit_limit = Column(Numeric(18, 2), default=0.0)
    overdue_credit_locked = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now)

    source_channel = relationship(
        "Channel",
        back_populates="users",
        primaryjoin="User.source_channel_id == Channel.id",
        foreign_keys=[source_channel_id],
        lazy="selectin",
    )
    loans = relationship(
        "Loan",
        back_populates="owner",
        cascade="all, delete-orphan",
        primaryjoin="User.id == Loan.user_id",
        foreign_keys="Loan.user_id",
        lazy="selectin",
    )
    events = relationship(
        "UserEvent",
        back_populates="user",
        cascade="all, delete-orphan",
        primaryjoin="User.id == UserEvent.user_id",
        foreign_keys="UserEvent.user_id",
        lazy="noload",
    )
