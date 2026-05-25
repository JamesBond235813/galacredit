from sqlalchemy import Boolean, Column, Integer, String, DateTime, Date, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # 状态：INIT, REVIEWING, APPROVED, REJECTED, WITHDRAWING, DISBURSED, SETTLED, OVERDUE
    status = Column(String(50), default="INIT", index=True)
    
    credit_limit = Column(Float, default=0.0)
    approved_credit_limit = Column(Float, default=0.0)
    fee_rate = Column(Float, default=0.6)         # 综合息费率
    fee_amount = Column(Float, default=0.0)       # 综合息费金额
    term_days = Column(Integer, nullable=True)     # 后台设定
    due_date = Column(DateTime, nullable=True)     # 后台发卡时根据 term_days 计算
    penalty_amount = Column(Float, default=0.0)    # 违约金
    repaid_amount = Column(Float, default=0.0)     # 已登记收款额
    reduction_amount = Column(Float, default=0.0)  # 已登记减免额
    other_fee_amount = Column(Float, default=0.0)  # 已登记其他费用
    paid_penalty_amount = Column(Float, default=0.0)
    reduced_penalty_amount = Column(Float, default=0.0)
    actual_repayment_date = Column(Date, nullable=True)  # 最近一次实际还款日期
    review_note = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0)
    last_reminded_at = Column(DateTime, nullable=True)
    collection_count = Column(Integer, default=0)
    last_collection_at = Column(DateTime, nullable=True)
    collection_note = Column(String(255), nullable=True)
    repay_attempt_count = Column(Integer, default=0)
    review_admin_id = Column(Integer, nullable=True, index=True)
    collection_admin_id = Column(Integer, nullable=True, index=True)
    collection_transferred_at = Column(DateTime, nullable=True)
    risk_report_checked_at = Column(DateTime, nullable=True)
    risk_report_checked_by = Column(String(50), nullable=True)
    approval_discount_amount = Column(Float, default=0.0)
    order_discount_amount = Column(Float, default=0.0)
    card_reissue_closed = Column(Boolean, default=False, nullable=False)
    extension_count = Column(Integer, default=0)
    extension_type = Column(String(30), nullable=True)
    extension_note = Column(String(255), nullable=True)
    overdue_hidden = Column(Boolean, default=False, nullable=False)
    extension_source_loan_id = Column(Integer, nullable=True, index=True)
    extension_used_at = Column(DateTime, nullable=True)
    is_extension_fee_order = Column(Boolean, default=False, nullable=False)
    identity_ocr_submitted_at = Column(DateTime, nullable=True)
    identity_face_auth_at = Column(DateTime, nullable=True)

    product_id = Column(Integer, nullable=True, index=True)
    product_name = Column(String(120), nullable=True)
    rights_title = Column(String(120), nullable=True)
    rights_desc = Column(String(255), nullable=True)
    rights_contact_phone = Column(String(20), nullable=True)
    rights_price = Column(Float, default=0.0)
    ecard_face_value = Column(Float, default=0.0)
    product_total_price = Column(Float, default=0.0)
    product_term_days = Column(Integer, nullable=True)

    ecard_account = Column(String(100), nullable=True)
    ecard_password = Column(String(100), nullable=True)
    ecard_expires_at = Column(DateTime, nullable=True)
    order_no = Column(String(32), nullable=False, default="")
    
    created_at = Column(DateTime, default=datetime.now) # 提现申请时间
    disbursed_at = Column(DateTime, nullable=True) # 发卡时间
    
    owner = relationship(
        "User",
        back_populates="loans",
        primaryjoin="Loan.user_id == User.id",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    review_admin = relationship(
        "Admin",
        primaryjoin="Loan.review_admin_id == Admin.id",
        foreign_keys=[review_admin_id],
        lazy="selectin",
    )
    collection_admin = relationship(
        "Admin",
        primaryjoin="Loan.collection_admin_id == Admin.id",
        foreign_keys=[collection_admin_id],
        lazy="selectin",
    )
    events = relationship(
        "UserEvent",
        back_populates="loan",
        cascade="all, delete-orphan",
        primaryjoin="Loan.id == UserEvent.loan_id",
        foreign_keys="UserEvent.loan_id",
        lazy="selectin",
    )
    installments = relationship(
        "LoanInstallment",
        back_populates="loan",
        cascade="all, delete-orphan",
        primaryjoin="Loan.id == LoanInstallment.loan_id",
        foreign_keys="LoanInstallment.loan_id",
        order_by="LoanInstallment.period_no",
        lazy="selectin",
    )
    transactions = relationship(
        "LoanTransaction",
        back_populates="loan",
        cascade="all, delete-orphan",
        primaryjoin="Loan.id == LoanTransaction.loan_id",
        foreign_keys="LoanTransaction.loan_id",
        order_by="LoanTransaction.created_at.desc()",
        lazy="selectin",
    )
    ecard_items = relationship(
        "LoanEcard",
        back_populates="loan",
        cascade="all, delete-orphan",
        primaryjoin="Loan.id == LoanEcard.loan_id",
        foreign_keys="LoanEcard.loan_id",
        order_by="LoanEcard.id.asc()",
        lazy="selectin",
    )
