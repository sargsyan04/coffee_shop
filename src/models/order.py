from typing import TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
from sqlalchemy import ForeignKey, Numeric, Integer, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.core.enums import OrderStatus

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.product import Product


class Order(BaseModel):

    # --> Fields <--
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status"),
        default=OrderStatus.CREATED,
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # --> User <--
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="orders")

    # --> Items <--
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    # --> Fields <--
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_at_order: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # --> Order <--
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order: Mapped["Order"] = relationship(back_populates="items")

    # --> Product <--
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product: Mapped["Product"] = relationship()
