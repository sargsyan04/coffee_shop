from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from src.core import UserRole
from src.schemas.common import EmailNormalizerMixin, PasswordComplexityMixin
from src.schemas.review import ReviewResponse

# Shared Fields


class UserBase(BaseModel, EmailNormalizerMixin):
    name: str
    email: EmailStr
    birth_date: date | None = None
    address: str | None = None
    phone: str | None = None


# Registration & Profile


class UserCreate(UserBase, PasswordComplexityMixin):
    password: str
    password_confirm: str
    force_new: bool = False

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class UserSettingsUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    birth_date: date | None = None


# Minimal user shape for embedding inside other responses
#     (e.g. a review's or order's author) — no email/phone/bonus points needed there
class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    image_url: str | None = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    is_active: bool
    is_email_verified: bool
    bonus_points: int
    image_url: str | None = None


# Token Responses


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


# Account Reactivation (soft-deleted accounts)


class ReactivateRequest(BaseModel, EmailNormalizerMixin):
    email: EmailStr


class UserPasswordChange(ReactivateRequest):
    code: str
    new_password: str


# Password Change (for already-logged-in users)


class ChangePasswordRequest(BaseModel):
    current_password: str | None = None
    new_password: str
    new_password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("Passwords do not match")
        return self


# Verification Code Resend & Account Status


class ResendCodeRequest(BaseModel, EmailNormalizerMixin):
    email: EmailStr


class UserStatusResponse(BaseModel):
    role: str
    is_active: bool
    is_email_verified: bool
    must_change_password: bool


# Admin User Management


class AdminUserResponse(UserResponse):
    email: str


class AdminUserStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    orders: dict[str, Decimal]
    total_spent: Decimal
    reviews: list[ReviewResponse]
    reviews_count: int
    orders_count: int


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserResetPassword(BaseModel):
    password: str
