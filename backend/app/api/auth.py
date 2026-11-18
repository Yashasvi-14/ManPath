
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    LoginRequest, 
    LoginResponse,
    RefreshRequest,
    LogoutRequest,
)
from app.services.token_service import (
    create_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token,
)
from app.core.security import create_access_token
from app.services.auth_service import register_user, verify_email, authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=202,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    register_user(
        db=db,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )

    return RegisterResponse(
        message=(
            "If registration can be completed, "
            "a verification email will be sent."
        )
    )


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=request.email,
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    try:
        access_token = create_access_token(str(user.id))

        refresh_token = create_refresh_token(
            db=db,
            user_id=user.id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    tokens = rotate_refresh_token(
        db=db,
        raw_token=request.refresh_token,
    )

    if tokens is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired, or revoked refresh token",
        )

    access_token, refresh_token = tokens

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
)
def verify_email_endpoint(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    verified = verify_email(
        db=db,
        raw_token=request.token,
    )

    if not verified:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token",
        )

    return VerifyEmailResponse(
        message="Email verified successfully",
    )


@router.post("/logout")
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
):
    revoked = revoke_refresh_token(
        db=db,
        raw_token=request.refresh_token,
    )

    if not revoked:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    return {
        "message": "Logged out successfully"
    }