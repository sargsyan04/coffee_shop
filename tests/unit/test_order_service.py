from src.core.enums import OrderStatus
from src.models import OrderItem
from src.services.order import complete_order


async def test_complete_order_sets_status_completed(db_session, user_factory, order_factory):
    user = await user_factory()
    order = await order_factory(user, status=OrderStatus.PAID)
    await db_session.refresh(order, attribute_names=["items"])

    await complete_order(db_session, order)

    assert order.status == OrderStatus.COMPLETED


async def test_complete_order_increases_product_sold_count(db_session, user_factory, product_factory, order_factory):
    user = await user_factory()
    product_a = await product_factory(sold_count=5)
    product_b = await product_factory(sold_count=0)
    order = await order_factory(user, status=OrderStatus.PAID)
    await db_session.refresh(order, attribute_names=["items"])

    # attach items straight to the in-memory relationship so complete_order
    # doesn't need to lazy-load order.items from the DB
    order.items.append(OrderItem(product_id=product_a.id, quantity=2))
    order.items.append(OrderItem(product_id=product_b.id, quantity=3))
    await db_session.commit()
    await db_session.refresh(order, attribute_names=["items"])

    await complete_order(db_session, order)

    await db_session.refresh(product_a)
    await db_session.refresh(product_b)
    assert product_a.sold_count == 7
    assert product_b.sold_count == 3


async def test_complete_order_with_no_items_just_updates_status(db_session, user_factory, order_factory):
    # an order with an empty item list shouldn't blow up on the sold_count loop
    user = await user_factory()
    order = await order_factory(user, status=OrderStatus.PAID)
    await db_session.refresh(order, attribute_names=["items"])

    await complete_order(db_session, order)

    assert order.status == OrderStatus.COMPLETED
