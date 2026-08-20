from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, Numeric, Boolean
from app.core.database import Base


class AdminLoginHistory(Base):
    """后台登录历史。"""
    __tablename__ = "admin_login_histories"
    id = Column(Integer, primary_key=True, comment="登录历史ID")
    admin_id = Column(Integer, nullable=False, index=True, comment="管理员ID")
    username = Column(String(50), nullable=False, comment="登录用户名")
    client_type = Column(String(20), nullable=False, default="WEB", comment="客户端类型")
    ip = Column(String(64), nullable=True, comment="登录IP")
    user_agent = Column(String(500), nullable=True, comment="客户端标识")
    success = Column(Boolean, nullable=False, default=True, comment="是否成功")
    failure_reason = Column(String(255), nullable=True, comment="失败原因")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="登录时间")


class ConfigChangeHistory(Base):
    """渠道或产品配置变更历史。"""
    __tablename__ = "config_change_histories"
    id = Column(Integer, primary_key=True, comment="变更历史ID")
    object_type = Column(String(20), nullable=False, index=True, comment="对象类型：CHANNEL或PRODUCT")
    object_id = Column(Integer, nullable=False, index=True, comment="对象ID")
    action = Column(String(20), nullable=False, comment="动作：CREATE、UPDATE、COPY")
    version_no = Column(Integer, nullable=False, default=1, comment="版本号")
    snapshot_json = Column(Text, nullable=False, comment="配置快照")
    operator_name = Column(String(50), nullable=True, comment="操作人")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="变更时间")


class MessageTemplate(Base):
    """消息模板及启停状态。"""
    __tablename__ = "message_templates"
    id = Column(Integer, primary_key=True, comment="模板ID")
    template_key = Column(String(80), nullable=False, index=True, comment="模板标识")
    version_no = Column(Integer, nullable=False, default=1, comment="模板版本")
    title = Column(String(120), nullable=False, comment="模板标题")
    content = Column(Text, nullable=False, comment="模板内容")
    is_active = Column(Boolean, nullable=False, default=True, index=True, comment="是否启用")
    created_by = Column(String(50), nullable=True, comment="创建人")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
