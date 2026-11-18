import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import MagicMock
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from app.services.token_service import rotate_refresh_token
from app.services.token_service import revoke_refresh_token
from app.core.security import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.services.token_service import create_refresh_token


def test_generate_refresh_token():
    token = generate_refresh_token()

    assert isinstance(token, str)
    assert len(token) > 50


def test_refresh_tokens_are_unique():
    first = generate_refresh_token()
    second = generate_refresh_token()

    assert first != second


def test_hash_refresh_token():
    token = generate_refresh_token()

    hashed = hash_refresh_token(token)

    assert len(hashed) == 64
    assert hashed != token


def test_same_refresh_token_produces_same_hash():
    token = generate_refresh_token()

    assert hash_refresh_token(token) == hash_refresh_token(token)


def test_create_refresh_token():
    db = MagicMock()
    user_id = uuid4()

    raw_token = create_refresh_token(
        db=db,
        user_id=user_id,
    )

    assert isinstance(raw_token, str)

    db.add.assert_called_once()

    stored_token = db.add.call_args.args[0]

    assert stored_token.user_id == user_id
    assert stored_token.token_hash == hash_refresh_token(raw_token)
    assert stored_token.token_hash != raw_token
    assert stored_token.family_id is not None
    assert stored_token.expires_at > datetime.now(timezone.utc)
    assert stored_token.used_at is None
    assert stored_token.revoked_at is None


def test_create_refresh_token_preserves_family():
    db = MagicMock()
    user_id = uuid4()
    family_id = uuid4()

    create_refresh_token(
        db=db,
        user_id=user_id,
        family_id=family_id,
    )

    stored_token = db.add.call_args.args[0]

    assert stored_token.family_id == family_id

def test_rotate_refresh_token_success():
    db = MagicMock()

    user_id = uuid4()
    family_id = uuid4()

    old_token = SimpleNamespace(
        user_id=user_id,
        family_id=family_id,
        used_at=None,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=10),
    )

    user = SimpleNamespace(
        id=user_id,
        is_active=True,
    )

    db.scalar.return_value = old_token
    db.get.return_value = user

    with patch(
        "app.services.token_service.create_refresh_token",
        return_value="new-refresh-token",
    ):
        with patch(
            "app.services.token_service.create_access_token",
            return_value="new-access-token",
        ):
            result = rotate_refresh_token(
                db=db,
                raw_token="old-refresh-token",
            )

    assert result == (
        "new-access-token",
        "new-refresh-token",
    )

    assert old_token.used_at is not None
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_reused_refresh_token_revokes_entire_family():
    db = MagicMock()

    family_id = uuid4()

    old_token = SimpleNamespace(
        family_id=family_id,
        used_at=datetime.now(timezone.utc),
        revoked_at=None,
    )

    db.scalar.return_value = old_token

    result = rotate_refresh_token(
        db=db,
        raw_token="previously-used-token",
    )

    assert result is None
    db.execute.assert_called_once()
    db.commit.assert_called_once()
    db.rollback.assert_not_called()

def test_expired_refresh_token_is_rejected():
    db = MagicMock()

    expired_token = SimpleNamespace(
        used_at=None,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )

    db.scalar.return_value = expired_token

    result = rotate_refresh_token(
        db=db,
        raw_token="expired-refresh-token",
    )

    assert result is None
    db.rollback.assert_called_once()
    db.commit.assert_not_called()
    db.get.assert_not_called()


def test_revoked_refresh_token_is_rejected():
    db = MagicMock()

    revoked_token = SimpleNamespace(
        used_at=None,
        revoked_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=10),
    )

    db.scalar.return_value = revoked_token

    result = rotate_refresh_token(
        db=db,
        raw_token="revoked-refresh-token",
    )

    assert result is None
    db.rollback.assert_called_once()
    db.commit.assert_not_called()
    db.get.assert_not_called()


def test_inactive_user_cannot_refresh_token():
    db = MagicMock()

    user_id = uuid4()

    stored_token = SimpleNamespace(
        user_id=user_id,
        family_id=uuid4(),
        used_at=None,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=10),
    )

    inactive_user = SimpleNamespace(
        id=user_id,
        is_active=False,
    )

    db.scalar.return_value = stored_token
    db.get.return_value = inactive_user

    result = rotate_refresh_token(
        db=db,
        raw_token="valid-refresh-token",
    )

    assert result is None
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_revoke_refresh_token_success():
    db = MagicMock()

    stored_token = SimpleNamespace(
        family_id=uuid4(),
    )

    db.scalar.return_value = stored_token

    result = revoke_refresh_token(
        db=db,
        raw_token="valid-refresh-token",
    )

    assert result is True
    db.execute.assert_called_once()
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_revoke_unknown_refresh_token():
    db = MagicMock()
    db.scalar.return_value = None

    result = revoke_refresh_token(
        db=db,
        raw_token="unknown-refresh-token",
    )

    assert result is False
    db.rollback.assert_called_once()
    db.commit.assert_not_called()