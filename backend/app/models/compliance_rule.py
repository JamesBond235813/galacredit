from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from app.core.database import Base


class ComplianceRule(Base):
    """贷款产品费用与披露的合规参数。"""

    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True, comment="合规规则ID")
    rule_name = Column(String(100), nullable=False, comment="规则名称")
    max_upfront_fee_rate = Column(Float, nullable=True, comment="上扣费用率上限")
    max_effective_apr = Column(Float, nullable=True, comment="折算年化费率上限")
    max_daily_overdue_fee = Column(Float, nullable=True, comment="每日逾期费上限")
    is_active = Column(Boolean, nullable=False, default=True, index=True, comment="是否启用")
    effective_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="生效时间")
    note = Column(String(255), nullable=True, comment="规则说明与法规依据")
    created_by = Column(String(50), nullable=True, comment="创建管理员")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
