from datetime import UTC, datetime, timedelta
import uuid
import bcrypt
from pydantic import SecretStr
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import jwt

from src.core import settings
from src.models import User
from src.models import RefreshToken

ACCESS_TOKEN_TYPE = "access_token"
REFRESH_TOKEN_TYPE = "refresh_token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")


def encode_jwt(payload: dict, key: SecretStr = settings.SECRET_KEY, algorithm: str = settings.ALGORITHM):
    return jwt.encode(payload=payload, key=key.get_secret_value(), algorithm=algorithm)


def decode_jwt(token: str, key: SecretStr = settings.SECRET_KEY, algorithm: str = settings.ALGORITHM):
    return jwt.decode(jwt=token, key=key.get_secret_value(), algorithms=[algorithm])


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), salt=bcrypt.gensalt())


def validate_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)


def create_jwt(token_type: str, token_data: dict) -> str:
    jwt_payload = {"token_type": token_type}
    jwt_payload.update(token_data)
    return encode_jwt(jwt_payload)


def verify_token(token: str, expected_type: str) -> dict:
    try:
        payload = decode_jwt(token)
        if payload.get("token_type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}"
            )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def create_verification_token(email: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=24)
    to_encode = {"sub": email, "exp": expire, "type": "email_verification"}
    return jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM)


def verify_email_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM])
        if payload.get("type") != "email_verification":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")


def create_access_token(user: User):
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expire
    }
    return create_jwt(ACCESS_TOKEN_TYPE, token_data)


async def create_refresh_token(session: AsyncSession, user: User) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token_id = str(uuid.uuid4())

    token_data = {
        "sub": str(user.id),
        "jti": token_id,
        "exp": expire
    }

    encoded_token = create_jwt(REFRESH_TOKEN_TYPE, token_data)

    db_token = RefreshToken(
        token=token_id,
        user_id=user.id,
        expires_at=expire
    )
    session.add(db_token)

    return encoded_token


async def generate_tokens(session: AsyncSession, user: User) -> dict:
    return {
        "access_token": create_access_token(user),
        "refresh_token": await create_refresh_token(session, user),
        "token_type": "bearer"
    }
