from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import db_session, settings
from src.models import User
from src.schemas import MessageResponse, ReactivateRequest, UserPasswordChange
from src.services import create_verification_token, hash_password, send_verification_email, verify_email_code

router = APIRouter()


@router.post("/reactivate", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def reactivate_account(
    payload: ReactivateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session),
):
    """Send a confirmation code to restart the reactivation of a deactivated account."""
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None or user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No deactivated account found for this email",
        )

    grace_period_end = user.deactivated_at + timedelta(days=settings.DEACTIVATION_GRACE_PERIOD_DAYS)
    if datetime.now(UTC) >= grace_period_end:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Reactivation period has expired")

    # Save values before create_verification_token, since it commits internally
    # and expires all objects currently tracked by the session
    user_id = user.id
    user_email = user.email

    code = await create_verification_token(session, user_id)
    background_tasks.add_task(send_verification_email, user_email, code)

    return {"detail": "Verification code sent. Confirm via POST /user/new-password to complete reactivation."}


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def forgot_password(
    payload: ReactivateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session),
):
    """Send a confirmation code to reset the password of an active account."""
    stmt = select(User).where(User.email == payload.email)
    user = await session.scalar(stmt)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active account found for this email",
        )

    # Save values before create_verification_token, since it commits internally
    # and expires all objects currently tracked by the session
    user_id = user.id
    user_email = user.email

    code = await create_verification_token(session, user_id)
    background_tasks.add_task(send_verification_email, user_email, code)

    return {"detail": "Verification code sent. Confirm via POST /user/new-password to set a new password."}


@router.post("/new-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def new_password(
    payload: UserPasswordChange,
    session: AsyncSession = Depends(db_session),
):
    """Confirm the reactivation code and set a new password, restoring the account."""
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verifies the code and marks it as used
    await verify_email_code(session, user.id, payload.code)
    await session.refresh(user)

    hashed_bytes = hash_password(payload.new_password)
    user.hashed_password = hashed_bytes.decode("utf-8")

    # If this account was deactivated, a verified code completes reactivation
    if not user.is_active:
        user.is_active = True
        user.deactivated_at = None

    await session.commit()

    return {"detail": "Password updated successfully. Please log in with your new password."}
