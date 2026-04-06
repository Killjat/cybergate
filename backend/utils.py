"""
加密工具
"""
from cryptography.fernet import Fernet
import os

# 生成或加载密钥
def get_encryption_key():
    key_file = "encryption_key.key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
    return key

cipher_suite = Fernet(get_encryption_key())

def encrypt_password(password: str) -> str:
    """加密密码"""
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """解密密码"""
    return cipher_suite.decrypt(encrypted_password.encode()).decode()
