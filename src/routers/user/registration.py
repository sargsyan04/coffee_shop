from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import UserRole, db_session, settings
from src.models import User
from src.schemas import MessageResponse, ResendCodeRequest, UserCreate, UserResponse, VerifyEmailRequest
from src.services import create_verification_token, hash_password, send_verification_email, verify_email_code
from src.validators import check_email_uniqueness

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session),
):
    """Create a new account and send the confirmation code by email."""
    existing_user = await check_email_uniqueness(session, payload.email)

    if existing_user:
        # An active account already owns this email
        if existing_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )

        # A deactivated account exists for this email
        grace_period_end = existing_user.deactivated_at + timedelta(days=settings.DEACTIVATION_GRACE_PERIOD_DAYS)

        if not payload.force_new and datetime.now(UTC) < grace_period_end:
            # Still within the grace period - offer reactivation instead of registration
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "An account with this email was deactivated recently.",
                    "reactivation_available": True,
                    "reactivation_deadline": grace_period_end.isoformat(),
                    "hint": "Use POST /user/reactivate with the same email to restore it.",
                },
            )

        # grace period expired — free up the email so a new account can take it.
        # Colons/spaces would make this an invalid email (breaks anything
        # serializing it through EmailStr, e.g. GET /admin/users), so keep
        # the timestamp URL/email-safe.
        deleted_at = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
        existing_user.email = f"deleted_user_{existing_user.id}_at_{deleted_at}@removed.email"
        await session.commit()

    # Hash the password before it ever touches the database
    hashed_password = hash_password(payload.password).decode("utf-8")

    new_user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hashed_password,
        phone=payload.phone,
        address=payload.address,
        birth_date=payload.birth_date,
        is_active=True,
        role=UserRole.CUSTOMER,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    user_id = new_user.id
    user_email = new_user.email

    code = await create_verification_token(session, user_id)
    background_tasks.add_task(send_verification_email, user_email, code)

    await session.refresh(new_user)
    return new_user


@router.post("/verify-email", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def verify_email(
    payload: VerifyEmailRequest,
    session: AsyncSession = Depends(db_session),
):
    """Confirm the email code, activating the account if it was pending or deactivated."""
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Only block re-verification for accounts that are already active
    if user.is_active and user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your email address has already been confirmed",
        )

    await verify_email_code(session, user.id, payload.code)
    await session.refresh(user)

    # If this account was deactivated, a successful code confirms reactivation
    if not user.is_active:
        user.is_active = True
        user.deactivated_at = None

    user.is_email_verified = True
    await session.commit()
    await session.refresh(user)

    return user


@router.post("/resend-code", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def resend_verification_code(
    payload: ResendCodeRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session),
):
    """Issue a fresh confirmation code for an account that hasn't verified its email yet."""
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your email address has already been confirmed",
        )

    # Save before create_verification_token, since it commits internally
    # and expires all objects currently tracked by the session
    user_id = user.id
    user_email = user.email

    code = await create_verification_token(session, user_id)
    background_tasks.add_task(send_verification_email, user_email, code)

    return {"detail": "A new verification code has been sent to your email."}
