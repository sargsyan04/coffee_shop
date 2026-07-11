from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    name: str
    email: EmailStr
    birth_date: date | None = None
    address: str | None = None
    phone: str | None = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    is_active: bool
    is_email_verified: bool
    bonus_points: int