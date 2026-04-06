"""
审计日志模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, index=True, nullable=False)  # 操作类型：create, update, delete, download, execute
    resource_type = Column(String, nullable=False)  # 资源类型：account, script
    resource_id = Column(Integer, nullable=True)  # 资源ID
    user = Column(String, nullable=True)  # 操作用户
    details = Column(Text, nullable=True)  # 操作详情（JSON格式）
    ip_address = Column(String, nullable=True)  # 操作IP
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, index=True, nullable=False)  # 账号ID
    platform = Column(String, nullable=False)  # 平台名称
    username = Column(String, nullable=False)  # 用户名
    action = Column(String, nullable=False)  # 动作：script_download, login_attempt
    success = Column(String, nullable=True)  # 是否成功
    error_message = Column(Text, nullable=True)  # 错误信息
    user = Column(String, nullable=True)  # 操作用户
    ip_address = Column(String, nullable=True)  # 操作IP
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
