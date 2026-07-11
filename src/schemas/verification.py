from pydantic import BaseModel, EmailStr

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str