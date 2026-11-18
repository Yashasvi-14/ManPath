import sys
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.core.database import get_db
from app.services.token_service import rotate_refresh_token, revoke_refresh_token

@pytest.fixture
def mock_db():
    db = MagicMock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    yield db

    app.dependency_overrides.clear()

@patch("app.api.auth.create_refresh_token")
@patch("app.api.auth.create_access_token")
@patch("app.api.auth.authenticate_user")
def test_login_success(
    mock_authenticate,
    mock_access_token,
    mock_refresh_token,
    mock_db,
):
    user = SimpleNamespace(id=uuid4())

    mock_authenticate.return_value = user
    mock_access_token.return_value = "test-access-token"
    mock_refresh_token.return_value = "test-refresh-token"

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": "manpath.test@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_type": "bearer",
    }

    mock_authenticate.assert_called_once()
    mock_access_token.assert_called_once_with(str(user.id))
    mock_refresh_token.assert_called_once_with(
        db=mock_db,
        user_id=user.id,
    )
    mock_db.commit.assert_called_once()

@patch("app.api.auth.authenticate_user")
def test_login_invalid_credentials(
    mock_authenticate,
    mock_db,
):
    mock_authenticate.return_value = None

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": "manpath.test@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

    mock_db.commit.assert_not_called()

@patch("app.api.auth.rotate_refresh_token")
def test_refresh_success(
    mock_rotate,
    mock_db,
):
    mock_rotate.return_value = (
        "new-access-token",
        "new-refresh-token",
    )

    client = TestClient(app)

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "old-refresh-token-value-123456",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }

    mock_rotate.assert_called_once_with(
        db=mock_db,
        raw_token="old-refresh-token-value-123456",
    )

@patch("app.api.auth.rotate_refresh_token")
def test_refresh_invalid_token(
    mock_rotate,
    mock_db,
):
    mock_rotate.return_value = None

    client = TestClient(app)

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid-refresh-token-value-123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid, expired, or revoked refresh token"
    )


@patch("app.api.auth.revoke_refresh_token")
def test_logout_success(mock_revoke, mock_db):
    mock_revoke.return_value = True

    client = TestClient(app)

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "valid-refresh-token-value-123456",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Logged out successfully"
    }

    mock_revoke.assert_called_once_with(
        db=mock_db,
        raw_token="valid-refresh-token-value-123456",
    )

@patch("app.api.auth.revoke_refresh_token")
def test_logout_invalid_token(mock_revoke, mock_db):
    mock_revoke.return_value = False

    client = TestClient(app)

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "invalid-refresh-token-value-123456",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"

def test_refresh_missing_token(mock_db):
    client = TestClient(app)

    response = client.post("/auth/refresh", json={})

    assert response.status_code == 422

def test_refresh_short_token(mock_db):
    client = TestClient(app)

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "short"},
    )

    assert response.status_code == 422

def test_logout_rejects_extra_fields(mock_db):
    client = TestClient(app)

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "valid-refresh-token-value-123456",
            "unexpected": "value",
        },
    )

    assert response.status_code == 422


