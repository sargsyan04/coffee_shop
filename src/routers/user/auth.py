from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import db_session, settings
from src.models import User
from src.schemas import MessageResponse, RefreshTokenRequest, TokenResponse
from src.services import generate_tokens, get_refresh_token_record
from src.validators import get_current_active_user, validate_password

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(db_session),
):
    """Exchange email/password credentials for an access and refresh token pair."""
    stmt = select(User).where(User.email == form_data.username)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    is_valid = validate_password(form_data.password, user.hashed_password.encode("utf-8"))
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Password confirmed - now it's safe to reveal account status
    if not user.is_active:
        grace_period_end = user.deactivated_at + timedelta(days=settings.DEACTIVATION_GRACE_PERIOD_DAYS)
        reactivation_available = datetime.now(UTC) < grace_period_end
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "This account has been deactivated.",
                "reactivation_available": reactivation_available,
                "reactivation_deadline": grace_period_end.isoformat() if reactivation_available else None,
                "hint": "Use POST /user/reactivate to restore it.",
            },
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email address not confirmed",
        )

    tokens = await generate_tokens(session, user)
    await session.commit()
    return tokens


@router.post("/refresh-token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(db_session),
):
    """Rotate a valid refresh token for a new access/refresh pair."""
    token = await get_refresh_token_record(payload, session)

    # Reject if the record is missing or already revoked
    if token is None or token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or does not exist",
        )

    # Extra expiry check at the database level
    if token.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")

    # Load the user this token belongs to
    user_stmt = select(User).where(User.id == token.user_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active")

    # Rotate: revoke the old refresh token and issue a brand new pair
    token.is_revoked = True

    new_tokens = await generate_tokens(session, user)
    await session.commit()

    return new_tokens


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(
    payload: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    """Revoke the given refresh token so it can no longer be used to obtain new access tokens."""
    token = await get_refresh_token_record(payload, session)

    if token is None or token.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    token.is_revoked = True

    await session.commit()

    return {"detail": "Logged out successfully."}
