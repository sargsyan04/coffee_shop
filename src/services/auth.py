from datetime import UTC, datetime, timedelta
import random
import uuid
import bcrypt
from pydantic import SecretStr
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import jwt

from src.core import settings
from src.models import User, RefreshToken, VerificationToken
from src.core.enums import VerificationTokenType

ACCESS_TOKEN_TYPE = "access_token"
REFRESH_TOKEN_TYPE = "refresh_token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")


# ============================================================
# --> JWT Encoding / Decoding <--
# ============================================================

def encode_jwt(payload: dict, key: SecretStr = settings.SECRET_KEY, algorithm: str = settings.ALGORITHM):
    return jwt.encode(payload=payload, key=key.get_secret_value(), algorithm=algorithm)


def decode_jwt(token: str, key: SecretStr = settings.SECRET_KEY, algorithm: str = settings.ALGORITHM):
    return jwt.decode(jwt=token, key=key.get_secret_value(), algorithms=[algorithm])


def create_jwt(token_type: str, token_data: dict) -> str:
    jwt_payload = {"token_type": token_type}
    jwt_payload.update(token_data)
    return encode_jwt(jwt_payload)


def verify_token(token: str, expected_type: str) -> dict:
    """Decodes the token and verifies its type (access vs refresh) matches
    what the caller expects. Raises 401 on any decoding failure."""
    try:
        payload = decode_jwt(token)
        if payload.get("token_type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}"
            )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ============================================================
# --> Password Hashing <--
# ============================================================

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), salt=bcrypt.gensalt())


# ============================================================
# --> Email Verification Codes (registration & reactivation) <--
# ============================================================

async def create_verification_token(session: AsyncSession, user_id: int) -> str:
    """Creates a 6-digit email verification code and stores it in the database."""

    # --> Step 1: invalidate any previous, still-unused codes for this user
    #     and this token type, before issuing a new one <--
    await session.execute(
        update(VerificationToken)
        .where(
            VerificationToken.user_id == user_id,
            VerificationToken.token_type == VerificationTokenType.EMAIL_CONFIRMATION,
            VerificationToken.is_used == False,
        )
        .values(is_used=True)
    )

    # --> Step 2: create the new code <--
    code = f"{random.randint(0, 999999):06d}"

    token = VerificationToken(
        user_id=user_id,
        code=code,
        token_type=VerificationTokenType.EMAIL_CONFIRMATION,
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )
    session.add(token)
    await session.commit()
    return code


async def verify_email_code(session: AsyncSession, user_id: int, code: str) -> bool:
    """Validates the submitted code and, if correct, marks it as used."""
    result = await session.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user_id,
            VerificationToken.code == code,
            VerificationToken.token_type == VerificationTokenType.EMAIL_CONFIRMATION,
            VerificationToken.is_used == False,
        )
    )
    token = result.scalar_one_or_none()

    if token is None:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    if token.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Verification code has expired")

    token.is_used = True
    await session.commit()
    return True


# ============================================================
# --> Access / Refresh Token Generation <--
# ============================================================

def create_access_token(user: User):
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data = {"sub": str(user.id), "email": user.email, "exp": expire}
    return create_jwt(ACCESS_TOKEN_TYPE, token_data)


async def create_refresh_token(session: AsyncSession, user: User) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token_id = str(uuid.uuid4())

    token_data = {"sub": str(user.id), "jti": token_id, "exp": expire}
    encoded_token = create_jwt(REFRESH_TOKEN_TYPE, token_data)

    db_token = RefreshToken(token=token_id, user_id=user.id, expires_at=expire)
    session.add(db_token)

    return encoded_token


async def generate_tokens(session: AsyncSession, user: User) -> dict:
    return {
        "access_token": create_access_token(user),
        "refresh_token": await create_refresh_token(session, user),
        "token_type": "bearer",
    }