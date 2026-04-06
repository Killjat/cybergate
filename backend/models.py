"""
数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"
    guest = "guest"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default=UserRole.user)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 分配的账号（普通用户）
    account_access = relationship("UserAccountAccess", back_populates="user")


class UserAccountAccess(Base):
    """普通用户可访问的账号"""
    __tablename__ = "user_account_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    user = relationship("User", back_populates="account_access")
    account = relationship("Account")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    two_factor_secret = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
