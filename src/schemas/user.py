from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict


# ============================================================
# --> Shared Fields <--
# ============================================================

class UserBase(BaseModel):
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

class ReactivateRequest(BaseModel):
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
    # --> current_password is optional: skipped when the account has
    #     must_change_password=True, since a valid access token already
    #     proves the caller knows the temporary password. <--
    current_password: str | None = None
    new_password: str