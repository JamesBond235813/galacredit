from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class LoanMandate(Base):
    """借款人的 MoMo 自动扣款授权记录。"""

    __tablename__ = "loan_mandates"

    id = Column(Integer, primary_key=True, index=True, comment="授权记录ID")
    loan_id = Column(Integer, nullable=True, index=True, comment="关联贷款订单ID")
    user_id = Column(Integer, nullable=False, index=True, comment="借款用户ID")
    provider = Column(String(40), nullable=False, default="momo", comment="支付服务商")
    mandate_reference = Column(String(120), nullable=True, unique=True, index=True, comment="服务商授权编号")
    status = Column(String(24), nullable=False, default="ACTIVE", index=True, comment="授权状态")
    consent_version = Column(String(40), nullable=False, default="v1", comment="授权文本版本")
    consent_content = Column(Text, nullable=False, comment="用户确认的授权文本快照")
    phone = Column(String(20), nullable=False, comment="授权使用的 MoMo 手机号")
    signed_at = Column(DateTime, nullable=False, default=datetime.now, comment="授权确认时间")
    revoked_at = Column(DateTime, nullable=True, comment="授权撤回时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
