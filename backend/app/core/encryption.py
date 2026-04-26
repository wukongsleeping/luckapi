"""API Key 加密模块，防止存储泄露。"""

import logging
import os
from base64 import urlsafe_b64encode
from hashlib import sha256

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def generate_encryption_key() -> str:
    """生成一个新的加密密钥用于轮换（当 SECRET_KEY 泄露时使用）。

    生成后需设置环境变量：API_KEY_ENCRYPTION_KEY=<生成的密钥>
    并执行数据重加密。
    """
    return Fernet.generate_key().decode()


# 加密密钥优先从独立环境变量 API_KEY_ENCRYPTION_KEY 获取
# 如果未配置，则基于 SECRET_KEY 派生（不推荐，会有安全风险）
_env_key = os.environ.get("API_KEY_ENCRYPTION_KEY", "")
if not _env_key:
    from app.core.config import get_settings

    settings = get_settings()
    _env_key = str(settings.SECRET_KEY)
    if _env_key:
        logger.warning(
            "API_KEY_ENCRYPTION_KEY 未配置，使用 SECRET_KEY 派生加密密钥。"
            "建议生成独立密钥并设置环境变量。"
        )
    else:
        logger.error("加密密钥不可用！请设置 API_KEY_ENCRYPTION_KEY 或 SECRET_KEY")
        raise RuntimeError("缺少加密密钥，请设置 API_KEY_ENCRYPTION_KEY 或 SECRET_KEY")

# Fernet 需要一个 32 字节的 Base64 URL-safe key
_fernet = Fernet(urlsafe_b64encode(sha256(_env_key.encode()).digest()))


def encrypt_api_key(plaintext: str) -> str:
    """加密 API Key"""
    if not plaintext:
        return ""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """解密 API Key。

    如果解密失败（旧数据 / 非 Fernet 格式），返回原文 -- 兼容未加密的历史数据。
    """
    if not ciphertext:
        return ""
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except Exception:
        if is_encrypted(ciphertext):
            logger.warning(
                "API Key 解密失败！可能是密钥已变更或数据被篡改。"
                "请立即检查 API_KEY_ENCRYPTION_KEY。"
            )
        return ciphertext  # 兼容旧数据 / 明文数据


def is_encrypted(value: str) -> bool:
    """判断值是否已加密"""
    if not value:
        return False
    try:
        _fernet.decrypt(value.encode())
        return True
    except Exception:
        return False
