from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import settings


def verify_google_id_token(token: str) -> dict | None:
    if not settings.google_client_id:
        raise RuntimeError("Google authentication is not configured")

    try:
        id_info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.google_client_id,
        )

        if id_info.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            return None

        if id_info.get("email_verified") is not True:
            return None

        if not id_info.get("sub") or not id_info.get("email"):
            return None

        return id_info

    except ValueError:
        return None