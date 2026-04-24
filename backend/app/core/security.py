import hashlib
import secrets
import string


def generate_api_key(prefix: str = "sk") -> str:
    """Generate a random API key like sk-xxxxxxxx..."""
    random_part = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(48)
    )
    return f"{prefix}-{random_part}"


def generate_user_token(user_id: int) -> str:
    """Generate a unique identifier for user lookup."""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    salt = "luckapi-salt"
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"sha256${salt}${h}"


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash.startswith("sha256$"):
        return False
    parts = password_hash.split("$")
    if len(parts) != 3:
        return False
    _, salt, h = parts
    expected = hashlib.sha256((salt + password).encode()).hexdigest()
    return expected == h
