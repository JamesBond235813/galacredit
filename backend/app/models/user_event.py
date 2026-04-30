from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserEvent(Base):
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    loan_id = Column(Integer, nullable=True, index=True)
    actor_type = Column(String(20), nullable=False, default="USER", index=True)
    operator_name = Column(String(50), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    user = relationship(
        "User",
        back_populates="events",
        primaryjoin="UserEvent.user_id == User.id",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    loan = relationship(
        "Loan",
        back_populates="events",
        primaryjoin="UserEvent.loan_id == Loan.id",
        foreign_keys=[loan_id],
        lazy="selectin",
    )
