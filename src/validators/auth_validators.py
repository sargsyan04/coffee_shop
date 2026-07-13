import bcrypt
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import db_session, UserRole
from src.models import User
from src.services import oauth2_scheme, decode_jwt, verify_token, ACCESS_TOKEN_TYPE


# ============================================================
# --> Registration Helpers <--
# ============================================================

async def check_email_uniqueness(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar()


def validate_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)


# ============================================================
# --> Authentication Dependencies (stacked, each builds on the previous) <--
# ============================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(db_session),
) -> User:
    """Identifies who the caller is. Does NOT check must_change_password —
    this is used by the password-change endpoint itself, which must remain
    reachable even for a locked account."""

    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token, ACCESS_TOKEN_TYPE)

    email = payload.get("email")
    if not email:
        raise exc

    stmt = select(User).where(User.email == email)
    current_user = await session.scalar(stmt)

    if current_user is None or not current_user.is_active:
        raise exc

    return current_user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Same as get_current_user, but additionally blocks access for accounts
    that must change their password first. Use this on every protected endpoint
    EXCEPT the password-change endpoint itself."""

    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "You must change your password before accessing this resource.",
                "must_change_password": True,
            }
        )
    return current_user


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Use this on admin-only endpoints. Requires the account to be fully
    unlocked (password already changed if it was required) AND to have
    the ADMIN role."""

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


async def require_staff(current_user: User = Depends(get_current_active_user)) -> User:
    """Use this on staff-only endpoints (baristas and admins).
    Broader than require_admin — lets baristas manage order statuses
    without granting full admin privileges."""

    if current_user.role not in (UserRole.BARISTA, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )

    return current_user
