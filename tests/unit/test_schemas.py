import pytest
from pydantic import ValidationError

from src.core import UserRole
from src.schemas.user import ChangePasswordRequest, ReactivateRequest, UserCreate, UserRoleUpdate


def _make_user_create(**overrides):
    fields = {
        "name": "Test User",
        "email": "Test@Example.com",
        "password": "secret123",
        "password_confirm": "secret123",
    }
    fields.update(overrides)
    return UserCreate(**fields)


def test_email_gets_lowercased():
    user = _make_user_create(email="Someone.Weird@EXAMPLE.com")

    assert user.email == "someone.weird@example.com"


def test_email_normalizer_applies_to_other_schemas_too():
    # EmailNormalizerMixin is shared - make sure it's not just wired up for UserCreate
    request = ReactivateRequest(email="CAPS@Example.com")

    assert request.email == "caps@example.com"


def test_user_create_matching_passwords_is_valid():
    user = _make_user_create(password="secret123", password_confirm="secret123")

    assert user.password == "secret123"


def test_user_create_mismatched_passwords_raises():
    with pytest.raises(ValidationError):
        _make_user_create(password="secret123", password_confirm="different")


def test_change_password_matching_passwords_is_valid():
    request = ChangePasswordRequest(
        current_password="old-pass",
        new_password="new-secret",
        new_password_confirm="new-secret",
    )

    assert request.new_password == "new-secret"


def test_change_password_mismatched_passwords_raises():
    with pytest.raises(ValidationError):
        ChangePasswordRequest(
            current_password="old-pass",
            new_password="new-secret",
            new_password_confirm="something-else",
        )


def test_user_role_update_accepts_known_role():
    update = UserRoleUpdate(role="admin")

    assert update.role == UserRole.ADMIN


def test_user_role_update_rejects_unknown_role():
    # this is exactly what the comment in schemas/user.py calls out - an
    # invalid role should be caught here (422), not reach the DB layer
    with pytest.raises(ValidationError):
        UserRoleUpdate(role="super_admin")
