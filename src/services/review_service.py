# src/services/review_service.py
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.review import Review
from src.models.order import Order, OrderItem
from src.models.product import Product
from src.core.enums import OrderStatus


async def can_leave_review(db: AsyncSession, user_id: int, product_id: int) -> bool:
    """Проверяет, покупал ли пользователь этот товар в завершённом заказе."""
    result = await db.execute(
        select(OrderItem)
        .join(Order)
        .where(
            Order.user_id == user_id,
            Order.status == OrderStatus.COMPLETED,
            OrderItem.product_id == product_id,
        )
    )
    return result.first() is not None


async def create_review(
    db: AsyncSession,
    user_id: int,
    product_id: int,
    rating: int,
    comment: str | None,
) -> Review:
    """Создаёт отзыв — но только если пользователь имеет на это право."""

    if not await can_leave_review(db, user_id, product_id):
        raise PermissionError("Отзыв можно оставить только на купленный и полученный товар")

    review = Review(
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    await recalculate_product_rating(db, product_id)

    return review


async def recalculate_product_rating(db: AsyncSession, product_id: int) -> None:
    """Пересчитывает средний рейтинг и количество отзывов товара после изменений."""
    result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id))
        .where(Review.product_id == product_id)
    )
    avg_rating, count = result.one()

    await db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(average_rating=avg_rating or 0, review_count=count)
    )
    await db.commit()