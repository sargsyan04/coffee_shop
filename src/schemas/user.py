from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict

from src.core import UserRole

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = UserRole.CUSTOMER
    birth_date: date | None
    address: str | None
    phone: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


    name: str
    email: EmailStr


