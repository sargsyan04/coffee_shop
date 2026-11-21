from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import OrderStatus
from src.models import Order, OrderItem, User


async def has_completed_order(session: AsyncSession, order: Order) -> bool:
    stmt = select(Order).where(Order.user_id == order.user_id, Order.status == OrderStatus.COMPLETED)

    return (await session.scalar(stmt)) is not None


async def order_list_by_user(session: AsyncSession, user_id: int) -> list[Order]:
    stmt = (
        select(Order)
        .where(
            Order.user_id == user_id,
            Order.status != OrderStatus.CREATED,
        )
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.desc())
    )

    orders = (await session.scalars(stmt)).all()

    return orders


async def add_bonus_points(session: AsyncSession, user_id: int, points: int) -> None:
    stmt = update(User).where(User.id == user_id).values(bonus_points=User.bonus_points + points)

    await session.execute(stmt)
