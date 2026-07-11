import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


async def check_email_uniqueness(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar()

def validate_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)