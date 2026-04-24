from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.mysql import LONGTEXT as LongText
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.core.encryption import encrypt_api_key, decrypt_api_key


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="", server_default=""
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user", server_default="user"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    balance: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
    total_usage: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
    allowed_ips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=utcnow
    )

    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    models: Mapped[list["UserModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="api_keys")


class UserModel(Base):
    __tablename__ = "user_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_url: Mapped[str] = mapped_column(String(500), nullable=False)
    _api_key: Mapped[str] = mapped_column(
        "api_key", String(500), nullable=False
    )  # 加密存储
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="models")

    @property
    def api_key(self) -> str:
        """获取解密的 API Key（用于代理转发）"""
        return decrypt_api_key(self._api_key)

    @api_key.setter
    def api_key(self, value: str):
        """设置 API Key（自动加密）"""
        self._api_key = encrypt_api_key(value)


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    _model_api_key: Mapped[Optional[str]] = mapped_column(
        "model_api_key", String(500), nullable=True
    )
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=utcnow
    )

    users: Mapped[list["GroupUser"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    @property
    def model_api_key(self) -> str:
        """获取解密的模型 Key"""
        if not self._model_api_key:
            return ""
        return decrypt_api_key(self._model_api_key)

    @model_api_key.setter
    def model_api_key(self, value: str):
        """设置模型 Key（自动加密）"""
        if not value:
            self._model_api_key = None
        else:
            self._model_api_key = encrypt_api_key(value)


class GlobalModel(Base):
    __tablename__ = "global_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_url: Mapped[str] = mapped_column(String(500), nullable=False)
    _api_key: Mapped[Optional[str]] = mapped_column(
        "api_key", String(500), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=utcnow
    )

    @property
    def api_key(self) -> str:
        """获取解密的 API Key"""
        if not self._api_key:
            return ""
        return decrypt_api_key(self._api_key)

    @api_key.setter
    def api_key(self, value: str):
        """设置 API Key（自动加密）"""
        if not value:
            self._api_key = None
        else:
            self._api_key = encrypt_api_key(value)


class GroupUser(Base):
    __tablename__ = "group_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    group: Mapped["Group"] = relationship(back_populates="users")
    user: Mapped["User"] = relationship()


class QaRecord(Base):
    __tablename__ = "qa_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    api_key_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False, default="POST")
    request_body: Mapped[str] = mapped_column(LongText, nullable=False)
    response_body: Mapped[str] = mapped_column(LongText, nullable=True)
    upstream_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
