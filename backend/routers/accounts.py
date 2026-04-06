"""
账号相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Account, UserAccountAccess, UserRole
from schemas import AccountCreate, AccountUpdate, AccountResponse
from utils import encrypt_password, decrypt_password
from utils_audit import log_audit_action
from auth import get_current_user, require_admin, get_current_user_optional

router = APIRouter()

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_accessible_accounts(user, db: Session):
    """根据角色返回可访问的账号列表"""
    if user is None or user.role == UserRole.guest:
        # 游客只能看第一个账号
        acc = db.query(Account).order_by(Account.id).first()
        return [acc] if acc else []
    if user.role == UserRole.admin:
        return db.query(Account).all()
    # 普通用户：只返回分配的账号
    access = db.query(UserAccountAccess).filter(UserAccountAccess.user_id == user.id).all()
    ids = [a.account_id for a in access]
    return db.query(Account).filter(Account.id.in_(ids)).all() if ids else []

@router.post("/", response_model=AccountResponse)
async def create_account(account: AccountCreate, request: Request, db: Session = Depends(get_db), user=Depends(require_admin)):
    """创建账号"""
    encrypted_password = encrypt_password(account.password)
    db_account = Account(
        platform=account.platform,
        username=account.username,
        password=encrypted_password,
        two_factor_secret=account.two_factor_secret,
        notes=account.notes
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    # 记录审计日志
    log_audit_action(
        db=db,
        action="create",
        resource_type="account",
        resource_id=db_account.id,
        user="web_user",
        details={"platform": account.platform, "username": account.username},
        ip_address=get_client_ip(request)
    )
    
    return db_account

@router.get("/", response_model=List[AccountResponse])
async def get_accounts(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    """获取账号列表（按角色过滤）"""
    accounts = get_accessible_accounts(user, db)
    return accounts

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, request: Request, db: Session = Depends(get_db)):
    """获取单个账号"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    # 记录审计日志
    log_audit_action(
        db=db,
        action="read",
        resource_type="account",
        resource_id=account_id,
        user="web_user",
        details={"platform": account.platform, "username": account.username},
        ip_address=get_client_ip(request)
    )
    
    return account

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: int, account_update: AccountUpdate, request: Request, db: Session = Depends(get_db), user=Depends(require_admin)):
    """更新账号"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    if account_update.platform:
        account.platform = account_update.platform
    if account_update.username:
        account.username = account_update.username
    if account_update.password:
        account.password = encrypt_password(account_update.password)
    if account_update.two_factor_secret is not None:
        account.two_factor_secret = account_update.two_factor_secret
    if account_update.notes is not None:
        account.notes = account_update.notes
    
    db.commit()
    db.refresh(account)
    
    # 记录审计日志
    log_audit_action(
        db=db,
        action="update",
        resource_type="account",
        resource_id=account_id,
        user="web_user",
        details={"platform": account.platform, "username": account.username},
        ip_address=get_client_ip(request)
    )
    
    return account

@router.delete("/{account_id}")
async def delete_account(account_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_admin)):
    """删除账号"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    platform = account.platform
    username = account.username
    
    db.delete(account)
    db.commit()
    
    # 记录审计日志
    log_audit_action(
        db=db,
        action="delete",
        resource_type="account",
        resource_id=account_id,
        user="web_user",
        details={"platform": platform, "username": username},
        ip_address=get_client_ip(request)
    )
    
    return {"message": "账号已删除"}

@router.get("/{account_id}/password")
async def get_decrypted_password(account_id: int, request: Request, db: Session = Depends(get_db)):
    """获取解密后的密码"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    # 记录审计日志（敏感操作）
    log_audit_action(
        db=db,
        action="decrypt_password",
        resource_type="account",
        resource_id=account_id,
        user="web_user",
        details={"platform": account.platform, "username": account.username},
        ip_address=get_client_ip(request)
    )
    
    return {"password": decrypt_password(account.password)}
