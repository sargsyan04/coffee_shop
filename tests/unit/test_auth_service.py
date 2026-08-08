from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from src.core.enums import VerificationTokenType
from src.models import VerificationToken
from src.schemas import RefreshTokenRequest
from src.services.auth import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_jwt,
    create_refresh_token,
    create_verification_token,
    generate_tokens,
    get_refresh_token_record,
    hash_password,
    verify_email_code,
    verify_token,
)

# Password Hashing


def test_hash_password_can_be_checked_with_bcrypt():
    import bcrypt

    hashed = hash_password("correct-horse")

    assert bcrypt.checkpw(b"correct-horse", hashed)
    assert not bcrypt.checkpw(b"wrong-password", hashed)


# JWT


async def test_create_and_verify_access_token(user_factory):
    user = await user_factory(email="jwt-user@example.com")

    token = create_access_token(user)
    payload = verify_token(token, ACCESS_TOKEN_TYPE)

    assert payload["email"] == user.email
    assert payload["sub"] == str(user.id)


async def test_verify_token_rejects_wrong_type(user_factory):
    user = await user_factory()
    token = create_access_token(user)

    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, REFRESH_TOKEN_TYPE)

    assert exc_info.value.status_code == 401


def test_verify_token_rejects_garbage_string():
    with pytest.raises(HTTPException) as exc_info:
        verify_token("not-a-real-token", ACCESS_TOKEN_TYPE)

    assert exc_info.value.status_code == 401


def test_verify_token_rejects_expired_token():
    expired_token = create_jwt(
        ACCESS_TOKEN_TYPE,
        {"sub": "1", "email": "x@example.com", "exp": datetime.now(UTC) - timedelta(minutes=1)},
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(expired_token, ACCESS_TOKEN_TYPE)

    assert exc_info.value.status_code == 401


# Refresh Tokens


async def test_create_refresh_token_stores_matching_db_row(db_session, user_factory):
    user = await user_factory()

    token = await create_refresh_token(db_session, user)
    await db_session.commit()

    payload = verify_token(token, REFRESH_TOKEN_TYPE)

    # look it up the same way get_refresh_token_record does, by the jti in the token
    request = RefreshTokenRequest(refresh_token=token)
    db_token = await get_refresh_token_record(request, db_session)

    assert db_token is not None
    assert db_token.user_id == user.id
    assert db_token.token == payload["jti"]


async def test_generate_tokens_returns_both_tokens(db_session, user_factory):
    user = await user_factory()

    tokens = await generate_tokens(db_session, user)
    await db_session.commit()

    assert tokens["token_type"] == "bearer"
    access_payload = verify_token(tokens["access_token"], ACCESS_TOKEN_TYPE)
    refresh_payload = verify_token(tokens["refresh_token"], REFRESH_TOKEN_TYPE)
    assert access_payload["email"] == user.email
    assert refresh_payload["sub"] == str(user.id)


async def test_get_refresh_token_record_returns_none_for_unknown_token(db_session):
    # a well-formed refresh token that was just never stored in the DB
    fake_token = create_jwt(
        REFRESH_TOKEN_TYPE,
        {"sub": "1", "jti": "does-not-exist", "exp": datetime.now(UTC) + timedelta(days=1)},
    )
    request = RefreshTokenRequest(refresh_token=fake_token)

    db_token = await get_refresh_token_record(request, db_session)

    assert db_token is None


# Email Verification Codes


async def test_verify_email_code_success_marks_token_used(db_session, user_factory):
    user = await user_factory()
    code = await create_verification_token(db_session, user.id)

    result = await verify_email_code(db_session, user.id, code)

    assert result is True

    from sqlalchemy import select

    stored = await db_session.scalar(select(VerificationToken).where(VerificationToken.code == code))
    assert stored.is_used is True


async def test_verify_email_code_wrong_code_raises(db_session, user_factory):
    user = await user_factory()
    await create_verification_token(db_session, user.id)

    with pytest.raises(HTTPException) as exc_info:
        await verify_email_code(db_session, user.id, "000000")

    assert exc_info.value.status_code == 400


async def test_verify_email_code_expired_raises(db_session, user_factory):
    user = await user_factory()

    expired = VerificationToken(
        user_id=user.id,
        code="123456",
        token_type=VerificationTokenType.EMAIL_CONFIRMATION,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    db_session.add(expired)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await verify_email_code(db_session, user.id, "123456")

    assert exc_info.value.status_code == 400


async def test_verify_email_code_cannot_be_used_twice(db_session, user_factory):
    user = await user_factory()
    code = await create_verification_token(db_session, user.id)

    await verify_email_code(db_session, user.id, code)

    with pytest.raises(HTTPException) as exc_info:
        await verify_email_code(db_session, user.id, code)

    assert exc_info.value.status_code == 400
