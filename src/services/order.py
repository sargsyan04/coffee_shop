from sqlalchemy.ext.asyncio import AsyncSession

from src.core import OrderStatus
from src.models import Order
from src.repositories import (
    add_bonus_points,
    get_order_by_id,
    product_count_update,
    update_order_status,
)
from src.services.bonus_points import calculate_bonus_points


async def complete_order(session: AsyncSession, order: Order) -> None:
    for item in order.items:
        await product_count_update(session, item.product_id, item.quantity)

    await update_order_status(session, order, OrderStatus.COMPLETED)

    await session.commit()


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await get_order_by_id(session, order_id)


async def order_status_change(session: AsyncSession, order: Order, status: OrderStatus) -> Order:
    # commit() expires every object in the session, so keep the plain int
    # and re-load the order (with items/product) for the response afterwards
    order_id = order.id

    if status == OrderStatus.COMPLETED:
        # Bonus points must be calculated BEFORE the status changes: the
        # "first order" check must not see this order as already completed
        if order.user_id is not None:
            total_items = sum(item.quantity for item in order.items)
            points = await calculate_bonus_points(session, order, total_items)

            await add_bonus_points(session, order.user_id, points)

        # Credit sold_count for every product in the order
        for item in order.items:
            await product_count_update(session, item.product_id, item.quantity)

    await update_order_status(session, order, status)

    await session.commit()

    return await get_order_by_id(session, order_id, refresh=True)
