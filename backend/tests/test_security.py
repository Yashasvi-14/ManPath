
import sys
from pathlib import Path

from datetime import datetime, timezone

import jwt

from app.core.config import settings
from app.core.security import create_access_token

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password, verify_password, decode_access_token


def test_password_is_hashed():
    password = "ManPath_Secure_Password_2026!"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")


def test_correct_password_is_verified():
    password = "ManPath_Secure_Password_2026!"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_incorrect_password_is_rejected():
    hashed = hash_password("CorrectPassword123!")

    assert verify_password("WrongPassword123!", hashed) is False


def test_same_password_produces_different_hashes():
    password = "ManPath_Secure_Password_2026!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)


def test_create_access_token_contains_user_id():
    user_id = "test-user-123"

    token = create_access_token(user_id)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == user_id


def test_access_token_contains_expiration():
    token = create_access_token("test-user-123")

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert "exp" in payload
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_access_token_contains_issued_at():
    token = create_access_token("test-user-123")

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert "iat" in payload

def test_decode_valid_access_token():
    user_id = "test-user-123"

    token = create_access_token(user_id)
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == user_id


def test_decode_invalid_token():
    payload = decode_access_token("invalid.token.value")

    assert payload is None


def test_decode_tampered_token():
    token = create_access_token("test-user-123")

    tampered_token = token[:-5] + "abcde"

    payload = decode_access_token(tampered_token)

    assert payload is None