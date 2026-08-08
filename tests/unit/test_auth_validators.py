import bcrypt
import pytest
from fastapi import HTTPException

from src.core import UserRole
from src.services.auth import create_access_token
from src.validators.auth import (
    check_email_uniqueness,
    get_current_active_user,
    get_current_user,
    require_admin,
    require_staff,
    validate_password,
)

# Registration Helpers


async def test_check_email_uniqueness_finds_existing_user(db_session, user_factory):
    user = await user_factory(email="taken@example.com")

    found = await check_email_uniqueness(db_session, "taken@example.com")

    assert found is not None
    assert found.id == user.id


async def test_check_email_uniqueness_returns_none_for_free_email(db_session):
    found = await check_email_uniqueness(db_session, "nobody@example.com")

    assert found is None


def test_validate_password_correct():
    hashed = bcrypt.hashpw(b"my-password", bcrypt.gensalt())

    assert validate_password("my-password", hashed) is True


def test_validate_password_incorrect():
    hashed = bcrypt.hashpw(b"my-password", bcrypt.gensalt())

    assert validate_password("wrong-password", hashed) is False


# get_current_user


async def test_get_current_user_with_valid_token(db_session, user_factory):
    user = await user_factory()
    token = create_access_token(user)

    current_user = await get_current_user(token=token, session=db_session)

    assert current_user.id == user.id


async def test_get_current_user_rejects_garbage_token(db_session):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="garbage", session=db_session)

    assert exc_info.value.status_code == 401


async def test_get_current_user_rejects_deactivated_account(db_session, user_factory):
    user = await user_factory(is_active=False)
    token = create_access_token(user)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, session=db_session)

    assert exc_info.value.status_code == 401


# get_current_active_user


async def test_get_current_active_user_allows_normal_account(user_factory):
    user = await user_factory()

    result = await get_current_active_user(current_user=user)

    assert result.id == user.id


async def test_get_current_active_user_blocks_forced_password_change(user_factory):
    user = await user_factory(must_change_password=True)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=user)

    assert exc_info.value.status_code == 403


# require_admin / require_staff


async def test_require_admin_allows_admin(user_factory):
    admin = await user_factory(role=UserRole.ADMIN)

    result = await require_admin(current_user=admin)

    assert result.id == admin.id


async def test_require_admin_blocks_customer(user_factory):
    customer = await user_factory(role=UserRole.CUSTOMER)

    with pytest.raises(HTTPException) as exc_info:
        await require_admin(current_user=customer)

    assert exc_info.value.status_code == 403


@pytest.mark.parametrize("role", [UserRole.BARISTA, UserRole.ADMIN])
async def test_require_staff_allows_barista_and_admin(user_factory, role):
    staff_user = await user_factory(role=role)

    result = await require_staff(current_user=staff_user)

    assert result.id == staff_user.id


async def test_require_staff_blocks_customer(user_factory):
    customer = await user_factory(role=UserRole.CUSTOMER)

    with pytest.raises(HTTPException) as exc_info:
        await require_staff(current_user=customer)

    assert exc_info.value.status_code == 403
