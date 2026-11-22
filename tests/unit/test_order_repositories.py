from decimal import Decimal

from src.core import OrderStatus
from src.models import Order, OrderItem, Product, User
from src.repositories import (
    add_bonus_points,
    create_guest_order,
    get_cart_by_user_id,
    get_order_by_id,
    product_count_update,
    update_order_status,
)
from src.services.order import complete_order


async def test_complete_order_credits_the_ordered_product_not_the_item_id(prod_like_session_factory):
    # product ids and order-item ids deliberately differ: item.id is NOT product_id
    async with prod_like_session_factory() as session:
        filler = Product(name="Filler", price=Decimal(1), is_available=True)
        latte = Product(name="Latte", price=Decimal(2), is_available=True, sold_count=0)
        user = User(email="a@b.c", hashed_password="x", name="U")
        session.add_all([filler, latte, user])
        await session.flush()
        order = Order(user_id=user.id, status=OrderStatus.PAID, total_price=Decimal(4))
        session.add(order)
        await session.flush()
        session.add(OrderItem(order_id=order.id, product_id=latte.id, quantity=2, price_at_order=latte.price))
        order_id, latte_id, filler_id = order.id, latte.id, filler.id
        await session.commit()

    async with prod_like_session_factory() as session:
        order = await get_order_by_id(session, order_id)
        await complete_order(session, order)

    async with prod_like_session_factory() as session:
        assert (await session.get(Product, latte_id)).sold_count == 2
        assert (await session.get(Product, filler_id)).sold_count == 0
        assert (await session.get(Order, order_id)).status == OrderStatus.COMPLETED


async def test_repositories_do_not_commit(prod_like_session_factory):
    async with prod_like_session_factory() as session:
        order = await create_guest_order(session, "Guest", "+37400000000", None)
        await update_order_status(session, order, OrderStatus.PAID)
        order_id = order.id
        # no commit here: leaving the session discards everything

    async with prod_like_session_factory() as session:
        assert await session.get(Order, order_id) is None


async def test_create_guest_order_fields(prod_like_session_factory):
    async with prod_like_session_factory() as session:
        order = await create_guest_order(session, "Guest", "+37400000000", "g@x.io")

        assert order.id is not None
        assert order.user_id is None
        assert order.status == OrderStatus.CREATED
        assert (order.guest_name, order.guest_phone, order.guest_email) == ("Guest", "+37400000000", "g@x.io")


async def test_get_order_by_id_refresh_overwrites_stale_data(prod_like_session_factory):
    async with prod_like_session_factory() as session:
        user = User(email="a@b.c", hashed_password="x", name="U")
        session.add(user)
        await session.flush()
        order = Order(user_id=user.id, status=OrderStatus.CREATED, total_price=Decimal(1))
        session.add(order)
        await session.flush()
        order_id = order.id
        await session.commit()

    async with prod_like_session_factory() as session, prod_like_session_factory() as other:
        loaded = await get_order_by_id(session, order_id)
        assert loaded.total_price == Decimal(1)

        (await other.get(Order, order_id)).total_price = Decimal(9)
        await other.commit()

        assert (await get_order_by_id(session, order_id)).total_price == Decimal(1)  # stale, identity map
        assert (await get_order_by_id(session, order_id, refresh=True)).total_price == Decimal(9)


async def test_get_cart_by_user_id_for_update_still_returns_the_cart(prod_like_session_factory):
    async with prod_like_session_factory() as session:
        user = User(email="a@b.c", hashed_password="x", name="U")
        session.add(user)
        await session.flush()
        session.add(Order(user_id=user.id, status=OrderStatus.CREATED, total_price=Decimal(0)))
        user_id = user.id
        await session.commit()

    async with prod_like_session_factory() as session:
        assert (await get_cart_by_user_id(session, user_id, for_update=True)) is not None
        assert (await get_cart_by_user_id(session, user_id + 100)) is None


async def test_product_count_update_and_add_bonus_points_are_atomic_increments(prod_like_session_factory):
    async with prod_like_session_factory() as session:
        product = Product(name="Latte", price=Decimal(2), is_available=True, sold_count=5)
        user = User(email="a@b.c", hashed_password="x", name="U", bonus_points=10)
        session.add_all([product, user])
        await session.flush()
        product_id, user_id = product.id, user.id
        await session.commit()

    async with prod_like_session_factory() as session:
        await product_count_update(session, product_id, 3)
        await add_bonus_points(session, user_id, 7)
        await session.commit()

    async with prod_like_session_factory() as session:
        assert (await session.get(Product, product_id)).sold_count == 8
        assert (await session.get(User, user_id)).bonus_points == 17
