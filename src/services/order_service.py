from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Product
from src.models.order import Order              # ← добавили
from src.core.enums import OrderStatus


async def complete_order(db: AsyncSession, order: Order):
    for item in order.items:
        await db.execute(
            update(Product)
            .where(Product.id == item.product_id)
            .values(sold_count=Product.sold_count + item.quantity)
        )
    order.status = OrderStatus.COMPLETED
    await db.commit()