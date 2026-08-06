from decimal import Decimal

import pytest

from src.core import OrderStatus
from src.models import OrderItem, Review
from src.services.review import can_leave_review, create_review, recalculate_product_rating


async def _add_order_item(db_session, order, product, quantity=1):
    item = OrderItem(order_id=order.id, product_id=product.id, quantity=quantity)
    db_session.add(item)
    await db_session.commit()


async def test_can_leave_review_when_purchased_and_completed(db_session, user_factory, product_factory, order_factory):
    user = await user_factory()
    product = await product_factory()
    order = await order_factory(user, status=OrderStatus.COMPLETED)
    await _add_order_item(db_session, order, product)

    assert await can_leave_review(db_session, user.id, product.id) is True


async def test_cannot_leave_review_without_purchase(db_session, user_factory, product_factory):
    user = await user_factory()
    product = await product_factory()

    assert await can_leave_review(db_session, user.id, product.id) is False


async def test_cannot_leave_review_if_order_not_completed(db_session, user_factory, product_factory, order_factory):
    user = await user_factory()
    product = await product_factory()
    order = await order_factory(user, status=OrderStatus.CREATED)
    await _add_order_item(db_session, order, product)

    assert await can_leave_review(db_session, user.id, product.id) is False


async def test_create_review_succeeds_when_allowed(db_session, user_factory, product_factory, order_factory):
    user = await user_factory()
    product = await product_factory()
    order = await order_factory(user, status=OrderStatus.COMPLETED)
    await _add_order_item(db_session, order, product)

    review = await create_review(db_session, user.id, product.id, rating=5, comment="Great coffee")

    assert review.id is not None
    assert review.user_id == user.id
    assert review.product_id == product.id
    assert review.rating == 5
    assert review.comment == "Great coffee"


async def test_create_review_raises_when_not_allowed(db_session, user_factory, product_factory):
    user = await user_factory()
    product = await product_factory()

    with pytest.raises(PermissionError):
        await create_review(db_session, user.id, product.id, rating=5, comment="Nice")


async def test_recalculate_product_rating(db_session, user_factory, product_factory):
    product = await product_factory()
    user_a = await user_factory()
    user_b = await user_factory()

    db_session.add_all(
        [
            Review(user_id=user_a.id, product_id=product.id, rating=4, comment="Good"),
            Review(user_id=user_b.id, product_id=product.id, rating=5, comment="Excellent"),
        ]
    )
    await db_session.commit()

    await recalculate_product_rating(db_session, product.id)
    await db_session.refresh(product)

    assert product.review_count == 2
    assert float(product.average_rating) == pytest.approx(4.5)
