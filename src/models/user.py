from typing import TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import String, Integer, Boolean, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.core import UserRole

if TYPE_CHECKING:
    from src.models.order import Order
    from src.models.review import Review
    from src.models.tokens import RefreshToken, VerificationToken


class User(BaseModel):

    # --> Step 1 — Required Account Information <--
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))

    # --> Step 2 — Optional Profile Information <--
    birth_date: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    address: Mapped[str | None] = mapped_column(String(500))

    # --> Account Status <--
    role: Mapped[UserRole] = mapped_column(default=UserRole.CUSTOMER)
    bonus_points: Mapped[int] = mapped_column(Integer(), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    # --> True right after the seeded admin account is created, or after a manual
    #     password reset by an admin. Forces the user to set a new password
    #     via PATCH /user/change-password before accessing any other endpoint. <--
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)

    # --> Service Fields <--
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # --> Relationships <--
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )