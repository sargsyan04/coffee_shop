from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from src.models.base import BaseModel
from src.models.associations import product_category_association

if TYPE_CHECKING:
    from src.models.category import Category

class Product(BaseModel):

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Integer())
    is_available: Mapped[bool] = mapped_column(Boolean(), default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean(), default=False)
    image_url: Mapped[str] = mapped_column(String(255))

    # relationships
    categories: Mapped[list["Category"]] = relationship(
        secondary=product_category_association,
        back_populates="products",
    )