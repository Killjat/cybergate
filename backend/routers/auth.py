"""
注册/登录 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserAccountAccess, UserRole, Account
from auth import hash_password, verify_password, create_token, get_current_user
from pydantic import BaseModel

router = APIRouter()

class RegisterBody(BaseModel):
    username: str
    password: str

class LoginBody(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(body: RegisterBody, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 第一个注册的用户自动成为 admin
    is_first = db.query(User).count() == 0
    role = UserRole.admin if is_first else UserRole.user

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role=role
    )
    db.add(user)
    db.flush()  # 获取 user.id

    # 普通用户默认分配第一个账号
    if role == UserRole.user:
        first_account = db.query(Account).order_by(Account.id).first()
        if first_account:
            db.add(UserAccountAccess(user_id=user.id, account_id=first_account.id))

    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.username, user.role)
    return {"token": token, "role": user.role, "username": user.username}

@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user.id, user.username, user.role)
    return {"token": token, "role": user.role, "username": user.username}

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "role": user.role}

@router.get("/guest-token")
def guest_token():
    """游客 token，role=guest"""
    # 游客用 id=0
    token = create_token(0, "guest", UserRole.guest)
    return {"token": token, "role": "guest", "username": "游客"}
