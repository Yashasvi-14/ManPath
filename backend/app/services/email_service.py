
from app.core.config import settings


def send_verification_email(email: str, token: str) -> None:
    """
    Development email adapter.

    Prints the verification link locally.
    Replace with an SMTP provider before production.
    """
    verification_url = (
        f"{settings.frontend_url}/verify-email?token={token}"
    )

    print("\n" + "=" * 55)
    print("MANPATH EMAIL VERIFICATION")
    print(f"Recipient: {email}")
    print(f"Verification link: {verification_url}")
    print("This link expires in 30 minutes.")
    print("=" * 55 + "\n")
