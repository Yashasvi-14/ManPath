from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User

def create_refresh_token(
    db: Session,
    user_id: UUID,
    family_id: UUID | None = None,
) -> str:
    raw_token = generate_refresh_token()

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        family_id=family_id or uuid4(),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )

    db.add(refresh_token)

    return raw_token



def rotate_refresh_token(
    db: Session,
    raw_token: str,
) -> tuple[str, str] | None:
    try:
        token_hash = hash_refresh_token(raw_token)

        stored_token = db.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )

        if stored_token is None:
            db.rollback()
            return None

        now = datetime.now(timezone.utc)

        # Reuse detection: revoke the entire session family.
        if stored_token.used_at is not None:
            db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.family_id == stored_token.family_id,
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            db.commit()
            return None

        if stored_token.revoked_at is not None:
            db.rollback()
            return None

        if stored_token.expires_at <= now:
            db.rollback()
            return None

        user = db.get(User, stored_token.user_id)

        if user is None or not user.is_active:
            db.rollback()
            return None

        stored_token.used_at = now

        new_refresh_token = create_refresh_token(
            db=db,
            user_id=user.id,
            family_id=stored_token.family_id,
        )

        new_access_token = create_access_token(str(user.id))

        db.commit()

        return new_access_token, new_refresh_token

    except Exception:
        db.rollback()
        raise



def revoke_refresh_token(
    db: Session,
    raw_token: str,
) -> bool:
    try:
        token_hash = hash_refresh_token(raw_token)

        stored_token = db.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )

        if stored_token is None:
            db.rollback()
            return False

        now = datetime.now(timezone.utc)

        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == stored_token.family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise
