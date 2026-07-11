from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.product import Product


class Category(BaseModel):
    __tablename__ = 'categories'

    # --> Fields <--
    name: Mapped[str] = mapped_column(String(120), unique=True)

    # --> Relationships <--
    products: Mapped[list["Product"]] = relationship(back_populates="category")