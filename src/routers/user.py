from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


from src.schemas import (
    UserResponse,
    UserCreate,
    VerifyEmailRequest,
    TokenResponse,
    ReactivateRequest,
    MessageResponse,
    UserPasswordChange,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ResendCodeRequest,
    UserStatusResponse,
)
from src.models import User, RefreshToken
from src.core import db_session, settings
from src.services import (
    create_verification_token,
    hash_password,
    send_verification_email,
    verify_email_code,
    generate_tokens,
    verify_token,
    REFRESH_TOKEN_TYPE,
)
from src.validators import check_email_uniqueness, validate_password, get_current_user, get_current_active_user
from src.core import UserRole

router = APIRouter(prefix="/user", tags=["Users"])


# ============================================================
# --> Registration & Email Verification <--
# ============================================================


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, background_tasks: BackgroundTasks, session: AsyncSession = Depends(db_session)):
    existing_user = await check_email_uniqueness(session, payload.email)

    if existing_user:
        # --> Case 1: an active account already owns this email <--
        if existing_user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email address already exists.")

        # --> Case 2: a deactivated account exists <--
        grace_period_end = existing_user.deactivated_at + timedelta(days=settings.DEACTIVATION_GRACE_PERIOD_DAYS)

        if datetime.now(UTC) < grace_period_end:
            # still within the grace period — offer reactivation instead of registration
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "An account with this email was deactivated recently.",
                    "reactivation_available": True,
                    "reactivation_deadline": grace_period_end.isoformat(),
                    "hint": "Use POST /user/reactivate with the same email and password to restore it.",
                },
            )

        # grace period expired — free up the email so a new account can take it
        existing_user.email = f"deleted-{existing_user.id}@removed.local"
        await session.commit()

    # --> Hash the password before it ever touches the database <--
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
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # --> Only block re-verification for accounts that are already active <--
    if user.is_active and user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your email address has already been confirmed")

    await verify_email_code(session, user.id, payload.code)
    await session.refresh(user)

    # --> If this account was deactivated, a successful code confirms reactivation <--
    if not user.is_active:
        user.is_active = True
        user.deactivated_at = None

    user.is_email_verified = True
    await session.commit()
    await session.refresh(user)

    return user


# ============================================================
# --> Login & Token Management <--
# ============================================================


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(db_session)):
    stmt = select(User).where(User.email == form_data.username)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    is_valid = validate_password(form_data.password, user.hashed_password.encode("utf-8"))
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    # --> Password confirmed — now it's safe to reveal account status <--
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Use POST /user/reactivate to restore it.",
        )

    if not user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address not confirmed")

    tokens = await generate_tokens(session, user)
    await session.commit()
    return tokens


@router.post("/refresh-token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(db_session),
):
    # --> Step 1: verify signature, expiry, and token type (must be refresh, not access) <--
    jwt_payload = verify_token(payload.refresh_token, REFRESH_TOKEN_TYPE)

    # --> Step 2: extract "jti" — the unique id we embedded when the token was created <--
    token_id = jwt_payload.get("jti")
    if not token_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # --> Step 3: find the matching record in the database <--
    stmt = select(RefreshToken).where(RefreshToken.token == token_id)
    result = await session.execute(stmt)
    db_token = result.scalar_one_or_none()

    # --> Step 4: reject if the record is missing or already revoked <--
    if db_token is None or db_token.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked or does not exist")

    # --> Step 5: extra expiry check at the database level <--
    if db_token.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")

    # --> Step 6: load the user this token belongs to <--
    user_stmt = select(User).where(User.id == db_token.user_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active")

    # --> Step 7: rotation — revoke the old refresh token, issue a brand new pair <--
    db_token.is_revoked = True

    new_tokens = await generate_tokens(session, user)
    await session.commit()

    return new_tokens


# ============================================================
# --> Account Reactivation (soft-deleted accounts) <--
# ============================================================


@router.post("/reactivate", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def reactivate_account(
    payload: ReactivateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session),
):
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None or user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No deactivated account found for this email")

    grace_period_end = user.deactivated_at + timedelta(days=settings.DEACTIVATION_GRACE_PERIOD_DAYS)
    if datetime.now(UTC) >= grace_period_end:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Reactivation period has expired")

    # --> Save values BEFORE create_verification_token, which commits internally
    #     and expires all objects currently tracked by the session <--
    user_id = user.id
    user_email = user.email

    code = await create_verification_token(session, user_id)
    background_tasks.add_task(send_verification_email, user_email, code)

    return {"detail": "Verification code sent. Confirm via POST /user/new-password to complete reactivation."}


@router.post("/new-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def new_password(
    payload: UserPasswordChange,
    session: AsyncSession = Depends(db_session),
):
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # --> Verifies the code AND marks it as used <--
    await verify_email_code(session, user.id, payload.code)
    await session.refresh(user)

    hashed_bytes = hash_password(payload.new_password)
    user.hashed_password = hashed_bytes.decode("utf-8")

    # --> If this account was deactivated, a verified code completes reactivation <--
    if not user.is_active:
        user.is_active = True
        user.deactivated_at = None

    await session.commit()

    return {"detail": "Password updated successfully. Please log in with your new password."}


# ============================================================
# --> Profile Management (requires an active account, password already set) <--
# ============================================================


@router.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/status", response_model=UserStatusResponse, status_code=status.HTTP_200_OK)
async def get_user_status(current_user: User = Depends(get_current_user)):
    return current_user


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(current_user: User = Depends(get_current_active_user), session: AsyncSession = Depends(db_session)):
    # --> Soft delete: deactivate instead of physically removing the row.
    #     Orders and reviews stay untouched — history is preserved for analytics. <--
    current_user.is_active = False
    current_user.deactivated_at = datetime.now(UTC)

    # --> Revoke all refresh tokens so a lingering token can't be used
    #     to obtain a new access token after deactivation <--
    await session.execute(update(RefreshToken).where(RefreshToken.user_id == current_user.id).values(is_revoked=True))

    await session.commit()


# ============================================================
# --> Password Change (reachable even when must_change_password is True) <--
# ============================================================


@router.patch("/change-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_session),
):
    if not current_user.must_change_password:
        # --> Regular password change: current_password is mandatory here <--
        if not payload.current_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is required.")

        is_valid = validate_password(payload.current_password, current_user.hashed_password.encode("utf-8"))
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

    hashed_bytes = hash_password(payload.new_password)
    current_user.hashed_password = hashed_bytes.decode("utf-8")
    current_user.must_change_password = False

    await session.commit()

    return {"detail": "Password changed successfully."}


# ============================================================
# --> Verification Code Resend <--
# ============================================================


@router.post("/resend-code", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def resend_verification_code(
    payload: ResendCodeRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session),
):
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your email address has already been confirmed")

    # --> Save before create_verification_token, which commits internally
    #     and expires all objects currently tracked by the session <--
    user_id = user.id
    user_email = user.email

    code = await create_verification_token(session, user_id)
    background_tasks.add_task(send_verification_email, user_email, code)

    return {"detail": "A new verification code has been sent to your email."}
