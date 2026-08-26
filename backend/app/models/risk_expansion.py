from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


class RiskManualOverride(Base):
    """风控人工覆盖记录。"""

    __tablename__ = "risk_manual_overrides"

    id = Column(Integer, primary_key=True, comment="人工覆盖ID")
    decision_id = Column(String(40), nullable=False, index=True, comment="决策流水号")
    action = Column(String(20), nullable=False, comment="覆盖动作：APPROVE、REFER、DECLINE、BLOCK")
    reason = Column(String(500), nullable=False, comment="覆盖原因")
    operator_id = Column(Integer, nullable=False, comment="操作者ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="创建时间")


class RiskDeviceSignal(Base):
    """设备、IP和速度特征快照。"""

    __tablename__ = "risk_device_signals"

    id = Column(Integer, primary_key=True, comment="特征记录ID")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    consent_granted = Column(Integer, nullable=False, default=0, comment="是否完成敏感信息授权")
    device_fingerprint = Column(String(128), nullable=True, index=True, comment="设备指纹")
    ip_address = Column(String(64), nullable=True, index=True, comment="IP地址")
    asn = Column(String(64), nullable=True, comment="网络ASN")
    is_proxy = Column(Integer, nullable=False, default=0, comment="是否代理网络")
    is_emulator = Column(Integer, nullable=False, default=0, comment="是否模拟器")
    application_count_24h = Column(Integer, nullable=False, default=0, comment="24小时申请次数")
    account_count_24h = Column(Integer, nullable=False, default=0, comment="24小时关联账户数")
    collected_channel = Column(String(30), nullable=False, default="H5", comment="采集来源")
    risk_level = Column(String(20), nullable=False, default="INFO", comment="风险等级")
    keyword_hits_json = Column(Text, nullable=False, comment="关键词命中JSON")
    sms_summary_json = Column(Text, nullable=False, comment="短信摘要JSON")
    app_summary_json = Column(Text, nullable=False, comment="应用列表摘要JSON")
    device_summary_json = Column(Text, nullable=False, comment="设备信息摘要JSON")
    risk_flags_json = Column(Text, nullable=False, comment="风险标记JSON")
    payload_json = Column(Text, nullable=False, comment="原始特征JSON")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="采集时间")


class RiskExternalCheck(Base):
    """外部数据查询及降级记录。"""

    __tablename__ = "risk_external_checks"

    id = Column(Integer, primary_key=True, comment="查询记录ID")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    provider = Column(String(80), nullable=False, comment="供应商标识")
    check_type = Column(String(40), nullable=False, comment="查询类型")
    status = Column(String(20), nullable=False, comment="状态：SKIPPED、SUCCESS、FAILED、REVIEW")
    score = Column(Numeric(8, 2), nullable=True, comment="外部评分")
    reason = Column(String(500), nullable=True, comment="结果说明")
    response_json = Column(Text, nullable=False, comment="脱敏响应JSON")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="查询时间")


class RiskModelScore(Base):
    """统计/机器学习模型评分记录。"""

    __tablename__ = "risk_model_scores"

    id = Column(Integer, primary_key=True, comment="模型评分ID")
    decision_id = Column(String(40), nullable=False, index=True, comment="决策流水号")
    model_key = Column(String(80), nullable=False, comment="模型标识")
    model_version = Column(String(40), nullable=False, comment="模型版本")
    score = Column(Numeric(8, 4), nullable=False, comment="模型评分")
    mode = Column(String(20), nullable=False, default="SHADOW", comment="执行模式")
    explanation_json = Column(Text, nullable=False, comment="解释因子JSON")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="评分时间")
