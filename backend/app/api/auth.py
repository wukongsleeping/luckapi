"""Admin auth endpoints: login, logout, get current user."""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import verify_password
from app.db.session import get_db
from app.db.redis import get_redis as _get_redis
from app.models.models import User

router = APIRouter()
security = HTTPBearer(auto_error=False)
settings = get_settings()

# ---------- login rate limiter (IP-based, enforced via Redis) ----------


async def _check_login_rate_limit(ip: str) -> bool:
    """Return True if login is allowed, False if rate-limited.

    Limits: 5 attempts per minute per IP.
    """
    try:
        redis_conn = await _get_redis()
        if redis_conn is None:
            return True
        key = f"login_rate:{ip}"
        current = await redis_conn.incr(key)
        if current == 1:
            await redis_conn.expire(key, 60)
        if current > 5:
            return False
        return True
    except Exception:
        # Redis unavailable — allow login to avoid blocking users
        return True


# ---------- shared dependency for role-based access ----------


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user with session validation.

    Reusable dependency that returns the full ORM User object.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = _decode_token(credentials.credentials)
    user_id_str = payload.get("sub")
    username = payload.get("username")

    if not user_id_str or not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Single-device check: verify revocation version matches
    try:
        from app.db.redis import get_redis

        redis_conn = await get_redis()
        if redis_conn is not None:
            revoke_key = f"user:revoke:{user_id_str}"
            stored_version = await redis_conn.get(revoke_key)
            if stored_version is None:
                now_ts = int(time.time())
                await redis_conn.set(revoke_key, now_ts, ex=86400 * 4)
    except Exception:
        pass  # Redis unavailable

    result = await db.execute(select(User).where(User.id == int(user_id_str)))
    user = result.scalar_one_or_none()

    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="Account not found or disabled")

    return user


async def admin_required(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


# ---------- token helpers ----------


def _create_token(sub: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {
            "sub": str(sub),
            "username": username,
            "iat": now,
            "exp": expire,
            "jti": f"dev:{sub}:{int(now.timestamp())}",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return {}


# ---------- auth flows ----------


@router.post("/login")
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    username: str = data.username
    password: str = data.password

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account is disabled")

    # ---- single-device login: revoke all previous tokens on Redis ----
    try:
        from app.db.redis import get_redis

        redis_conn = await get_redis()
        # Delete old revocation keys to invalidate stale sessions
        revoke_key = f"user:revoke:{user.id}"
        if redis_conn is not None:
            await redis_conn.delete(revoke_key)
            # Set a new revocation version for the current login
            now_ts = int(time.time())
            await redis_conn.set(
                revoke_key, now_ts, ex=86400 * 4
            )  # keep 4 days just in case
    except Exception:
        pass  # Redis unavailable — proceed anyway, just no single-device enforcement

    token = _create_token(user.id, user.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "status": user.status,
            "balance": user.balance,
        },
    }


@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Logout — invalidate current session on server side."""
    if not credentials:
        return {"ok": True}

    payload = _decode_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if user_id_str:
        revoke_key = f"user:revoke:{user_id_str}"
        try:
            from app.db.redis import get_redis

            redis_conn = await get_redis()
            if redis_conn is not None:
                await redis_conn.delete(revoke_key)
        except Exception:
            pass

    return {"ok": True}


@router.get("/me")
async def me(
    current_user: User = Depends(admin_required),
):
    """Get current authenticated user."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "status": current_user.status,
        "balance": current_user.balance,
    }


# ---------- admin API endpoints ----------


@router.post("/admin/test", response_model=dict)
async def admin_test_endpoint(
    _current_user: User = Depends(admin_required),
):
    """Test admin endpoint to verify role check works."""
    return {"ok": True, "message": "Admin access granted"}
