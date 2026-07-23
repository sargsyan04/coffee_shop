from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.core.enums import VerificationTokenType
from src.models.mixins import DateMixin

if TYPE_CHECKING:
    from src.models.user import User


class VerificationToken(BaseModel):
    __tablename__ = "verification_tokens"

    # --> Fields <--
    code: Mapped[str] = mapped_column(String(10))
    token_type: Mapped[VerificationTokenType] = mapped_column()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # --> User <--
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="verification_tokens")


class RefreshToken(BaseModel, DateMixin):
    __tablename__ = "refresh_tokens"

    # --> Fields <--
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --> User <--
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
