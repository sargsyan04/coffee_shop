from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import OrderStatus
from src.models import Order, OrderItem


async def orders_list(session: AsyncSession) -> list[Order]:

    stmt = (
        select(Order)
        .where(Order.status.in_((OrderStatus.PAID, OrderStatus.IN_PROGRESS, OrderStatus.READY)))
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.asc())
    )

    orders = (await session.scalars(stmt)).all()

    return orders
