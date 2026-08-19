from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class LoanEcard(Base):
    __tablename__ = "loan_ecards"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, nullable=False, index=True)
    ecard_pool_id = Column(Integer, nullable=False, index=True)
    account = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    face_value = Column(Numeric(18, 2), default=0.0, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    loan = relationship(
        "Loan",
        back_populates="ecard_items",
        primaryjoin="LoanEcard.loan_id == Loan.id",
        foreign_keys=[loan_id],
        lazy="selectin",
    )
