"""
审计日志工具
"""
from sqlalchemy.orm import Session
from models_audit import AuditLog, AccessLog
from datetime import datetime
import json
import socket

def log_audit_action(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: int = None,
    user: str = "anonymous",
    details: dict = None,
    ip_address: str = None
):
    """记录审计日志"""
    if ip_address is None:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except:
            ip_address = "unknown"
    
    audit_log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user=user,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        created_at=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log

def log_access_action(
    db: Session,
    account_id: int,
    platform: str,
    username: str,
    action: str,
    success: bool = None,
    error_message: str = None,
    user: str = "anonymous",
    ip_address: str = None
):
    """记录访问日志"""
    if ip_address is None:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except:
            ip_address = "unknown"
    
    access_log = AccessLog(
        account_id=account_id,
        platform=platform,
        username=username,
        action=action,
        success="success" if success else "failed" if success is not None else None,
        error_message=error_message,
        user=user,
        ip_address=ip_address,
        created_at=datetime.utcnow()
    )
    db.add(access_log)
    db.commit()
    db.refresh(access_log)
    return access_log
