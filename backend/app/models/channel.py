from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String(32), unique=True, index=True, nullable=False)
    invite_code = Column(String(32), unique=True, index=True, nullable=False, default="", comment="渠道邀请码")
    sales_name = Column(String(50), nullable=False)
    status = Column(String(20), default="ACTIVE", index=True, nullable=False)
    disbursement_mode = Column(
        String(24),
        default="MANUAL_DISBURSE",
        index=True,
        nullable=False,
        comment="渠道放款模式：AUTO_DISBURSE 自动放款，MANUAL_DISBURSE 人工放款",
    )
    review_mode = Column(
        String(20),
        default="MANUAL_REVIEW",
        index=True,
        nullable=False,
        comment="渠道审核模式：AUTO_REVIEW 自动审核，MANUAL_REVIEW 人工审核",
    )
    note = Column(String(255), nullable=True)
    admin_user_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    users = relationship(
        "User",
        back_populates="source_channel",
        primaryjoin="Channel.id == User.source_channel_id",
        foreign_keys="User.source_channel_id",
        lazy="selectin",
    )
