from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.associations import product_tag_association

if TYPE_CHECKING:
    from src.models.product import Product


class Tag(BaseModel):

    name: Mapped[str] = mapped_column(String(50), unique=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)

    products: Mapped[list["Product"]] = relationship(
        secondary=product_tag_association,
        back_populates="tags",
    )