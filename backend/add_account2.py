"""
添加第二个 Google 账号
"""
from database import SessionLocal
from models import Account
from utils import encrypt_password

def add_account():
    db = SessionLocal()

    # 创建第二个 Google 账号
    encrypted_password = encrypt_password("Qwe1220010579.")
    account = Account(
        platform="google",
        username="YardFribley@gmail.com",
        password=encrypted_password,
        two_factor_secret="2l2x44n6kiayie3ikkbtnwin4y5a7ftl",
        notes="Google 账号 2"
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    print(f"账号添加成功！账号 ID: {account.id}")
    db.close()

if __name__ == "__main__":
    add_account()
