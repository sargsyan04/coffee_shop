from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Order
from src.repositories import order_list_by_user


async def user_orders_list(session: AsyncSession, user) -> list[Order]:

    return await order_list_by_user(session, user.id)
