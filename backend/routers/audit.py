"""
审计日志相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database import get_db
from models_audit import AuditLog, AccessLog

router = APIRouter()

def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.get("/audit-logs", response_model=List[dict])
async def get_audit_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: str = None,
    resource_type: str = None,
    db: Session = Depends(get_db)
):
    """获取审计日志"""
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    # 记录查询操作
    from utils_audit import log_audit_action
    log_audit_action(
        db=db,
        action="query",
        resource_type="audit_log",
        user="web_user",
        details={"count": len(logs)},
        ip_address=get_client_ip(request)
    )
    
    return [
        {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "user": log.user,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]

@router.get("/access-logs", response_model=List[dict])
async def get_access_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    account_id: int = None,
    platform: str = None,
    action: str = None,
    db: Session = Depends(get_db)
):
    """获取访问日志"""
    query = db.query(AccessLog)
    
    if account_id:
        query = query.filter(AccessLog.account_id == account_id)
    if platform:
        query = query.filter(AccessLog.platform == platform)
    if action:
        query = query.filter(AccessLog.action == action)
    
    logs = query.order_by(AccessLog.created_at.desc()).offset(skip).limit(limit).all()
    
    # 记录查询操作
    from utils_audit import log_audit_action
    log_audit_action(
        db=db,
        action="query",
        resource_type="access_log",
        user="web_user",
        details={"count": len(logs)},
        ip_address=get_client_ip(request)
    )
    
    return [
        {
            "id": log.id,
            "account_id": log.account_id,
            "platform": log.platform,
            "username": log.username,
            "action": log.action,
            "success": log.success,
            "error_message": log.error_message,
            "user": log.user,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]

@router.get("/stats", response_model=dict)
async def get_statistics(request: Request, db: Session = Depends(get_db)):
    """获取统计信息"""
    from models import Account
    from sqlalchemy import func
    
    total_accounts = db.query(Account).count()
    total_audit_logs = db.query(AuditLog).count()
    total_access_logs = db.query(AccessLog).count()
    
    # 按平台统计
    platforms = db.query(Account.platform, func.count(Account.id)).group_by(Account.platform).all()
    platform_stats = {platform: count for platform, count in platforms}
    
    # 最近7天的访问统计
    from datetime import timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_access = db.query(AccessLog).filter(AccessLog.created_at >= seven_days_ago).count()
    
    return {
        "total_accounts": total_accounts,
        "total_audit_logs": total_audit_logs,
        "total_access_logs": total_access_logs,
        "platform_stats": platform_stats,
        "recent_access_count": recent_access
    }
