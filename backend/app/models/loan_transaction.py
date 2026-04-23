from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class LoanTransaction(Base):
    __tablename__ = "loan_transactions"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_type = Column(String(30), nullable=False, index=True)
    amount = Column(Float, default=0.0, nullable=False)

    principal_amount = Column(Float, default=0.0, nullable=False)
    interest_amount = Column(Float, default=0.0, nullable=False)
    guarantee_fee_amount = Column(Float, default=0.0, nullable=False)
    penalty_amount = Column(Float, default=0.0, nullable=False)

    operator_name = Column(String(50), nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    loan = relationship("Loan", back_populates="transactions")
    user = relationship("User")
