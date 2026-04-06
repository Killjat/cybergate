"""
数据模型
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AccountBase(BaseModel):
    platform: str
    username: str
    password: str
    two_factor_secret: Optional[str] = None
    notes: Optional[str] = None

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    platform: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    two_factor_secret: Optional[str] = None
    notes: Optional[str] = None

class AccountResponse(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime
    password: str  # 加密后的密码

    class Config:
        from_attributes = True
