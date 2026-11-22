from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Product


async def get_product_by_id(session: AsyncSession, product_id: int) -> Product | None:
    stmt = select(Product).where(Product.id == product_id)

    return await session.scalar(stmt)


async def get_products_list(session: AsyncSession, product_ids: list[int]) -> dict:
    products_stmt = select(Product).where(Product.id.in_(product_ids))

    products = {p.id: p for p in (await session.scalars(products_stmt)).all()}

    return products


async def product_count_update(session: AsyncSession, product_id: int, quantity: int) -> None:
    stmt = update(Product).where(Product.id == product_id).values(sold_count=Product.sold_count + quantity)

    await session.execute(stmt)
