"""
添加测试账号
"""
from database import SessionLocal
from models import Account
from utils import encrypt_password

def add_account():
    db = SessionLocal()

    # 创建 Google 账号
    encrypted_password = encrypt_password("Qwe1220010579.")
    account = Account(
        platform="google",
        username="KeltnerAvon@gmail.com",
        password=encrypted_password,
        two_factor_secret="ikhhzr5azzy32yqs4itsncpvf2qhbqbi",
        notes="Google 账号"
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    print(f"账号添加成功！账号 ID: {account.id}")
    db.close()

if __name__ == "__main__":
    add_account()
