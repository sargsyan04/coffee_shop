from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import OrderStatus
from src.models.order import Order, OrderItem
from src.models.product import Product
from src.models.review import Review


async def can_leave_review(db: AsyncSession, user_id: int, product_id: int) -> bool:
    """Checks whether the user bought this product in a completed order."""
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
    """Creates a review — but only if the user is allowed to."""
    if not await can_leave_review(db, user_id, product_id):
        raise PermissionError("A review can only be left for a product you have purchased and received")

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
    """Recalculates the product's average rating and review count after changes."""
    result = await db.execute(select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product_id))
    avg_rating, count = result.one()

    await db.execute(update(Product).where(Product.id == product_id).values(average_rating=avg_rating or 0, review_count=count))
    await db.commit()
