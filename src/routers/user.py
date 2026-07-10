from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import UserResponse, UserCreate
from src.models import User
from src.core import db_session
from src.validators import check_email_uniqueness
from src.core import UserRole

router = APIRouter(prefix="/user", tags=["Users"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
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

    new_user = User(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        password=hashed_bytes,
        is_active=False,
        role=UserRole.CUSTOMER
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    token = create_verification_token(new_user.email)
    background_tasks.add_task(send_verification_email, new_user.email, token)

    return {"detail": "Registration successful. Please check your email to verify your account."}

