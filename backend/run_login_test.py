"""
直接测试 Google 自动登录
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import Account
from utils import decrypt_password

def main():
    account_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    db = SessionLocal()
    account = db.query(Account).filter(Account.id == account_id).first()
    db.close()

    if not account:
        print(f"未找到 id={account_id} 的账号")
        return

    password = decrypt_password(account.password)
    print(f"账号: {account.username}")
    print(f"平台: {account.platform}")
    print(f"2FA: {'已配置' if account.two_factor_secret else '未配置'}")
    print("开始登录...\n")

    # 直接调用登录函数（同步方式运行）
    import asyncio
    from routers.auto_login import auto_login_google
    result = asyncio.run(auto_login_google(
        account.username,
        password,
        account.two_factor_secret
    ))
    print(f"\n结果: {result}")

if __name__ == "__main__":
    main()
