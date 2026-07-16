from pydantic import BaseModel, EmailStr

from src.schemas.common import EmailNormalizerMixin


class VerifyEmailRequest(BaseModel, EmailNormalizerMixin):
    email: EmailStr
    code: str