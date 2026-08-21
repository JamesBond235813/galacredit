from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


class RiskPolicyVersion(Base):
    """风控策略版本。"""

    __tablename__ = "risk_policy_versions"

    id = Column(Integer, primary_key=True, comment="策略版本ID")
    policy_key = Column(String(80), nullable=False, index=True, comment="策略标识")
    version_no = Column(Integer, nullable=False, comment="策略版本号")
    status = Column(String(20), nullable=False, default="SHADOW", index=True, comment="状态：DRAFT、SHADOW、ACTIVE、DISABLED")
    config_json = Column(Text, nullable=False, comment="策略配置JSON")
    rollout_percent = Column(Integer, nullable=False, default=0, comment="灰度比例百分比")
    created_by = Column(String(50), nullable=True, comment="创建人")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")


class RiskDecision(Base):
    """一次风控决策及其可重放快照。"""

    __tablename__ = "risk_decisions"

    id = Column(Integer, primary_key=True, comment="决策ID")
    decision_id = Column(String(40), nullable=False, unique=True, index=True, comment="决策流水号")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    loan_id = Column(Integer, nullable=True, index=True, comment="订单ID")
    stage = Column(String(30), nullable=False, index=True, comment="决策阶段：APPLICATION、ORDER、DISBURSEMENT、REVIEW")
    decision = Column(String(20), nullable=False, index=True, comment="决策结果")
    score = Column(Numeric(8, 2), nullable=True, comment="综合风险分，越高风险越高")
    policy_key = Column(String(80), nullable=False, comment="策略标识")
    policy_version = Column(String(30), nullable=False, comment="策略版本")
    mode = Column(String(20), nullable=False, default="SHADOW", comment="执行模式：SHADOW、ENFORCE")
    reason_codes_json = Column(Text, nullable=False, comment="标准原因码JSON数组")
    feature_snapshot_json = Column(Text, nullable=False, comment="特征快照JSON")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="决策时间")


class RiskRuleHit(Base):
    """单次风控决策命中的规则。"""

    __tablename__ = "risk_rule_hits"

    id = Column(Integer, primary_key=True, comment="规则命中ID")
    decision_id = Column(String(40), nullable=False, index=True, comment="决策流水号")
    rule_code = Column(String(80), nullable=False, index=True, comment="规则编码")
    outcome = Column(String(20), nullable=False, comment="规则结果：PASS、REFER、DECLINE、BLOCK")
    severity = Column(String(20), nullable=False, default="INFO", comment="严重级别")
    detail = Column(String(500), nullable=True, comment="规则命中说明")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="命中时间")
