from pydantic import BaseModel, field_validator


class MessageResponse(BaseModel):
    detail: str


class EmailNormalizerMixin:
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()
