from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Numeric

from app.core.database import Base


class MomoTransaction(Base):
    """MoMo 资金交易流水，记录请求、回调与最终状态。"""

    __tablename__ = "momo_transactions"

    id = Column(Integer, primary_key=True, index=True, comment="MoMo流水ID")
    loan_id = Column(Integer, nullable=False, index=True, comment="关联贷款订单ID")
    user_id = Column(Integer, nullable=False, index=True, comment="借款用户ID")
    transaction_type = Column(String(24), nullable=False, index=True, comment="交易类型：DISBURSEMENT或REPAYMENT")
    provider = Column(String(40), nullable=False, default="mock", comment="支付服务商")
    provider_reference = Column(String(120), nullable=True, unique=True, index=True, comment="服务商流水号")
    idempotency_key = Column(String(120), nullable=False, unique=True, index=True, comment="幂等键")
    phone = Column(String(20), nullable=False, comment="MoMo手机号")
    amount = Column(Numeric(18, 2), nullable=False, default=0, comment="交易金额")
    status = Column(String(24), nullable=False, default="PENDING", index=True, comment="交易状态")
    request_payload = Column(Text, nullable=True, comment="请求报文快照")
    response_payload = Column(Text, nullable=True, comment="服务商响应报文快照")
    callback_payload = Column(Text, nullable=True, comment="回调报文快照")
    failure_message = Column(String(255), nullable=True, comment="失败原因")
    requested_at = Column(DateTime, nullable=False, default=datetime.now, comment="发起时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
