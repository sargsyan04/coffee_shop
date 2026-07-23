from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import settings, UserRole
from src.services import hash_password
from src.models import User


async def seed_admin_user(session: AsyncSession) -> None:
    """Creates the initial admin account if no admin exists yet.
    Runs once on application startup — safe to call every time,
    it simply does nothing if an admin is already present."""

    stmt = select(User).where(User.role == UserRole.ADMIN)
    result = await session.execute(stmt)
    existing_admin = result.scalar()

    if existing_admin is not None:
        return  # an admin already exists — nothing to do

    hashed_bytes = hash_password(settings.ADMIN_PASSWORD)

    admin = User(
        name=settings.ADMIN_NAME,
        email=settings.ADMIN_EMAIL,
        hashed_password=hashed_bytes.decode("utf-8"),
        role=UserRole.ADMIN,
        is_active=True,
        is_email_verified=True,  # skip email verification for the seeded admin
        must_change_password=True,  # force a password change on first login
    )

    session.add(admin)
    await session.commit()

    print(f"[SEED] Initial admin account created: {settings.ADMIN_EMAIL}")
