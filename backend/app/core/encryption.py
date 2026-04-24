"""API Key 加密模块，防止存储泄露。"""

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken as _InvalidToken
from app.core.config import get_settings
import os

from hashlib import sha256
from base64 import urlsafe_b64encode

settings = get_settings()

# 从环境变量获取加密密钥；如果没有则基于 SECRET_KEY 派生一个 Fernet-compatible key
raw_key = os.environ.get("API_KEY_ENCRYPTION_KEY", str(settings.SECRET_KEY))
# Fernet 需要一个 32 字节的 Base64 URL-safe key
fernet_key = urlsafe_b64encode(sha256(raw_key.encode()).digest())
_fernet = Fernet(fernet_key)


def encrypt_api_key(plaintext: str) -> str:
    """加密 API Key"""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """解密 API Key。

    如果解密失败（旧数据/非 Fernet 格式），返回原文——兼容未加密的历史数据。
    """
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except (_InvalidToken, ValueError, TypeError):
        return ciphertext


def is_encrypted(value: str) -> bool:
    """判断值是否已加密"""
    try:
        _fernet.decrypt(value.encode())
        return True
    except Exception:
        return False
