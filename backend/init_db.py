"""
初始化数据库
"""
from database import engine, Base
from models import Account
from models_audit import AuditLog, AccessLog

# 创建所有表
Base.metadata.create_all(bind=engine)

print("数据库初始化完成！")
