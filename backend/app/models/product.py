from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, Numeric

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    ecard_face_value = Column(Numeric(18, 2), default=0.0, nullable=False)
    rights_price = Column(Numeric(18, 2), default=0.0, nullable=False)
    rights_title = Column(String(120), nullable=False, default="韶关丹霞山旅游权益")
    rights_desc = Column(Text, nullable=True)
    rights_detail_json = Column(Text, nullable=True)
    term_days = Column(Integer, nullable=False, default=7)
    payment_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    nominal_loan_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    upfront_fee_rate = Column(Numeric(8, 6), default=0.4, nullable=False)
    fee_components_json = Column(Text, nullable=True)
    interest_start_day = Column(Integer, default=1, nullable=False)
    repayment_due_day = Column(Integer, default=7, nullable=False)
    installment_count = Column(Integer, default=1, nullable=False)
    installment_ratios_json = Column(Text, nullable=True)
    daily_overdue_fee = Column(Numeric(18, 2), default=10.0, nullable=False)
    borrower_type = Column(
        String(16),
        default="ALL",
        nullable=False,
        index=True,
        comment="适用借款人类型：NEW 新用户，REPEAT 复借用户，ALL 通用",
    )
    product_type = Column(String(30), default="ECARD_RIGHTS", nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
