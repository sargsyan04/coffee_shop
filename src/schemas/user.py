from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict, model_validator

from src.schemas.common import EmailNormalizerMixin

# ============================================================
# --> Shared Fields <--
# ============================================================


class UserBase(BaseModel, EmailNormalizerMixin):
    name: str
    email: EmailStr
    birth_date: date | None = None
    address: str | None = None
    phone: str | None = None


# ============================================================
# --> Registration & Profile <--
# ============================================================


class UserCreate(UserBase):
    password: str
    password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    is_active: bool
    is_email_verified: bool
    bonus_points: int


# ============================================================
# --> Token Responses <--
# ============================================================


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


# ============================================================
# --> Account Reactivation (soft-deleted accounts) <--
# ============================================================


class ReactivateRequest(BaseModel, EmailNormalizerMixin):
    email: EmailStr


class UserPasswordChange(ReactivateRequest):
    # --> Used by POST /user/new-password. Verifies the emailed code
    #     AND sets a new password in a single step. <--
    code: str
    new_password: str


# ============================================================
# --> Password Change (for already-logged-in users) <--
# ============================================================


class ChangePasswordRequest(BaseModel):
    current_password: str | None = None
    new_password: str
    new_password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("Passwords do not match")
        return self


# ============================================================
# --> Verification Code Resend & Account Status <--
# ============================================================


class ResendCodeRequest(BaseModel, EmailNormalizerMixin):
    email: EmailStr


class UserStatusResponse(BaseModel):
    role: str
    is_active: bool
    is_email_verified: bool
    must_change_password: bool
