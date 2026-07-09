from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.associations import product_category_association

if TYPE_CHECKING:
    from src.models.product import Product

class Category(BaseModel):
    __tablename__ = 'categories'

    name: Mapped[str] = mapped_column(String(120))

    products: Mapped[list["Product"]] = relationship(
        secondary=product_category_association,
        back_populates="categories",
    )
