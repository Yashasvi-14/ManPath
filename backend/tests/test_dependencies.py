from uuid import uuid4
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.models.user import User

def test_missing_credentials():
    db = Mock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=None, db=db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Authentication required"


def test_invalid_token():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid.token",
    )

    db = Mock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=credentials, db=db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired token"


def test_valid_token_returns_user():
    user_id = uuid4()

    user = User(
        id=user_id,
        email="test@example.com",
        full_name="Test User",
        is_active=True,
    )

    token = create_access_token(str(user_id))

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    db = Mock()
    db.get.return_value = user

    result = get_current_user(credentials=credentials, db=db)

    assert result == user
    db.get.assert_called_once_with(User, user_id)


def test_inactive_user_rejected():
    user_id = uuid4()

    inactive_user = User(
        id=user_id,
        email="inactive@example.com",
        full_name="Inactive User",
        is_active=False,
    )

    token = create_access_token(str(user_id))

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    db = Mock()
    db.get.return_value = inactive_user

    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=credentials, db=db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "User not found or inactive"