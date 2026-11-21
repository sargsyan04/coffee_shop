from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Order
from src.repositories import orders_list


async def orders_for_staff(session: AsyncSession) -> list[Order]:

    return await orders_list(session)
