
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.email_verification_token import EmailVerificationToken
from app.services.email_service import send_verification_email


VERIFICATION_TOKEN_EXPIRY_MINUTES = 30


def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
) -> None:
    normalized_email = email.strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    # Avoid revealing whether an account already exists.
    if existing_user:
        return

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES
    )

    user = User(
        email=normalized_email,
        hashed_password=hash_password(password),
        full_name=full_name.strip(),
        is_active=False,
        email_verified_at=None,
    )

    verification_token = EmailVerificationToken(
        token_hash=token_hash,
        expires_at=expires_at,
    )

    user.email_verification_tokens.append(verification_token)

    try:
        db.add(user)
        db.commit()

    except IntegrityError:
        db.rollback()
        # Handles concurrent registration attempts for the same email.
        return

    # Send only after the database transaction succeeds.
    send_verification_email(normalized_email, raw_token)


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    normalized_email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None or user.hashed_password is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active or user.email_verified_at is None:
        return None

    return user


def verify_email(db: Session, raw_token: str) -> bool:
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    try:
        verification = db.scalar(
            select(EmailVerificationToken)
            .where(
                EmailVerificationToken.token_hash == token_hash
            )
            .with_for_update()
        )

        if verification is None:
            return False

        now = datetime.now(timezone.utc)

        if verification.used_at is not None:
            return False

        if verification.expires_at <= now:
            return False

        user = db.scalar(
            select(User)
            .where(User.id == verification.user_id)
            .with_for_update()
        )

        if user is None or user.is_active:
            return False

        user.is_active = True
        user.email_verified_at = now
        verification.used_at = now

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

