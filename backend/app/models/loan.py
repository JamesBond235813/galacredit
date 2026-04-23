from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 状态：INIT, REVIEWING, APPROVED, REJECTED, WITHDRAWING, DISBURSED, SETTLED, OVERDUE
    status = Column(String(50), default="INIT", index=True)
    
    credit_limit = Column(Float, default=0.0)
    approved_credit_limit = Column(Float, default=0.0)
    fee_rate = Column(Float, default=0.6)         # 综合息费率
    fee_amount = Column(Float, default=0.0)       # 综合息费金额
    term_days = Column(Integer, nullable=True)     # 后台设定
    due_date = Column(DateTime, nullable=True)     # 后台放款时根据 term_days 计算
    penalty_amount = Column(Float, default=0.0)    # 违约金
    repaid_amount = Column(Float, default=0.0)     # 已登记收款额
    reduction_amount = Column(Float, default=0.0)  # 已登记减免额
    paid_penalty_amount = Column(Float, default=0.0)
    reduced_penalty_amount = Column(Float, default=0.0)
    review_note = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0)
    last_reminded_at = Column(DateTime, nullable=True)
    collection_count = Column(Integer, default=0)
    last_collection_at = Column(DateTime, nullable=True)
    collection_note = Column(String(255), nullable=True)
    repay_attempt_count = Column(Integer, default=0)
    review_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True, index=True)
    collection_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True, index=True)
    collection_transferred_at = Column(DateTime, nullable=True)

    product_id = Column(Integer, nullable=True, index=True)
    product_name = Column(String(120), nullable=True)
    rights_title = Column(String(120), nullable=True)
    rights_desc = Column(String(255), nullable=True)
    rights_price = Column(Float, default=0.0)
    ecard_face_value = Column(Float, default=0.0)
    product_total_price = Column(Float, default=0.0)
    product_term_days = Column(Integer, nullable=True)

    ecard_account = Column(String(100), nullable=True)
    ecard_password = Column(String(100), nullable=True)
    ecard_expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow) # 提现申请时间
    disbursed_at = Column(DateTime, nullable=True) # 放款时间
    
    owner = relationship("User", back_populates="loans")
    review_admin = relationship("Admin", foreign_keys=[review_admin_id])
    collection_admin = relationship("Admin", foreign_keys=[collection_admin_id])
    events = relationship("UserEvent", back_populates="loan", cascade="all, delete-orphan")
    installments = relationship(
        "LoanInstallment",
        back_populates="loan",
        cascade="all, delete-orphan",
        order_by="LoanInstallment.period_no",
    )
    transactions = relationship(
        "LoanTransaction",
        back_populates="loan",
        cascade="all, delete-orphan",
        order_by="LoanTransaction.created_at.desc()",
    )
