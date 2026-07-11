from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.product import Product
    from src.models.user import User


class Review(BaseModel):
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_review"),
    )

    # --> Fields <--
    rating: Mapped[int] = mapped_column(Integer)   # 1–5
    comment: Mapped[str | None] = mapped_column(String(500))

    # --> User <--
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="reviews")

    # --> Product <--
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product: Mapped["Product"] = relationship(back_populates="reviews")