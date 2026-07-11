from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import UserResponse, UserCreate
from src.models import User
from src.core import db_session
from src.services import create_verification_token, hash_password, send_verification_email
from src.validators import check_email_uniqueness
from src.core import UserRole

router = APIRouter(prefix="/user", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session)
):
    existing_user = await check_email_uniqueness(session, body.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    hashed_bytes = hash_password(body.password)
    hashed_password = hashed_bytes.decode("utf-8")

    new_user = User(
        name=body.name,
        email=body.email,
        hashed_password=hashed_password,
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