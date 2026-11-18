import secrets
import hashlib
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 15

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password using the recommended Argon2 configuration."""
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a password against its stored hash."""
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        return payload

    except jwt.InvalidTokenError:
        return None


def generate_refresh_token() -> str:
    """Generate a cryptographically secure opaque refresh token."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Return the SHA-256 hash of a refresh token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()