from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class LoanInstallment(Base):
    __tablename__ = "loan_installments"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False, index=True)
    period_no = Column(Integer, nullable=False, index=True)
    due_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="PENDING", nullable=False, index=True)

    principal_amount = Column(Float, default=0.0, nullable=False)
    interest_amount = Column(Float, default=0.0, nullable=False)
    guarantee_fee_amount = Column(Float, default=0.0, nullable=False)
    due_amount = Column(Float, default=0.0, nullable=False)

    paid_principal_amount = Column(Float, default=0.0, nullable=False)
    paid_interest_amount = Column(Float, default=0.0, nullable=False)
    paid_guarantee_fee_amount = Column(Float, default=0.0, nullable=False)
    paid_amount = Column(Float, default=0.0, nullable=False)

    reduced_principal_amount = Column(Float, default=0.0, nullable=False)
    reduced_interest_amount = Column(Float, default=0.0, nullable=False)
    reduced_guarantee_fee_amount = Column(Float, default=0.0, nullable=False)
    reduction_amount = Column(Float, default=0.0, nullable=False)

    settled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    loan = relationship("Loan", back_populates="installments")
