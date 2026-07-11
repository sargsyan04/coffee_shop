from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import UserResponse, UserCreate, VerifyEmailRequest, UserLogin, TokenResponse
from src.models import User
from src.core import db_session
from src.services import (
    create_verification_token, hash_password, send_verification_email, verify_email_code,
    generate_tokens
)
from src.validators import check_email_uniqueness, validate_password
from src.core import UserRole

router = APIRouter(prefix="/user", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session)
):
    existing_user = await check_email_uniqueness(session, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    hashed_bytes = hash_password(payload.password)
    hashed_password = hashed_bytes.decode("utf-8")

    new_user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hashed_password,
        phone = payload.phone,
        address = payload.address,
        birth_date = payload.birth_date,
        is_active=True,
        role=UserRole.CUSTOMER,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # сохраняем нужные значения В ОБЫЧНЫЕ переменные,
    # пока объект ещё не "протух" от следующего commit()
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
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_email_verified:
        raise HTTPException(status_code=400, detail="Your email address has already been confirmed")

    await verify_email_code(session, user.id, payload.code)

    user.is_email_verified = True
    await session.commit()
    await session.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(payload: UserLogin, session: AsyncSession = Depends(db_session)):
    stmt = select(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    is_valid = validate_password(payload.password, user.hashed_password.encode("utf-8"))
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address not confirmed")

    tokens = await generate_tokens(session, user)
    await session.commit()
    return tokens
