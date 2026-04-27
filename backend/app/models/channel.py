from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String(32), unique=True, index=True, nullable=False)
    sales_name = Column(String(50), nullable=False)
    status = Column(String(20), default="ACTIVE", index=True, nullable=False)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship(
        "User",
        back_populates="source_channel",
        primaryjoin="Channel.id == User.source_channel_id",
        foreign_keys="User.source_channel_id",
        lazy="selectin",
    )
