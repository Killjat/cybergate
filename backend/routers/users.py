"""
用户管理 API（管理员）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserAccountAccess, Account
from auth import require_admin, get_current_user
from typing import List

router = APIRouter()

@router.get("/")
def list_users(db: Session = Depends(get_db), admin=Depends(require_admin)):
    users = db.query(User).all()
    result = []
    for u in users:
        access_ids = [a.account_id for a in u.account_access]
        result.append({
            "id": u.id, "username": u.username, "role": u.role,
            "account_ids": access_ids, "created_at": u.created_at
        })
    return result

@router.put("/{user_id}/accounts")
def set_user_accounts(user_id: int, body: dict, db: Session = Depends(get_db), admin=Depends(require_admin)):
    """设置用户可访问的账号列表"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    account_ids: List[int] = body.get("account_ids", [])

    # 删旧的，加新的
    db.query(UserAccountAccess).filter(UserAccountAccess.user_id == user_id).delete()
    for acc_id in account_ids:
        if db.query(Account).filter(Account.id == acc_id).first():
            db.add(UserAccountAccess(user_id=user_id, account_id=acc_id))
    db.commit()
    return {"user_id": user_id, "account_ids": account_ids}

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.query(UserAccountAccess).filter(UserAccountAccess.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"message": "已删除"}
