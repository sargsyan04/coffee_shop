from typing import TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.associations import product_tag_association

if TYPE_CHECKING:
    from src.models.category import Category
    from src.models.tag import Tag
    from src.models.review import Review


class Product(BaseModel):

    # --> Fields <--
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_available: Mapped[bool] = mapped_column(Boolean(), default=False)
    image_url: Mapped[str | None] = mapped_column(String(255))

    # --> Aggregated Stats (denormalized for fast reads) <--
    average_rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    review_count: Mapped[int] = mapped_column(Integer(), default=0)
    sold_count: Mapped[int] = mapped_column(Integer(), default=0)

    # --> Category <--
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="products")

    # --> Tag <--
    tags: Mapped[list["Tag"]] = relationship(
        secondary=product_tag_association,
        back_populates="products",
    )

    # --> Review <--
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")
