from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from src.core import OrderStatus, UserRole
from src.core import db_session as get_db_session
from src.main import app
from src.models import Order, OrderItem, Product, User
from src.validators import get_current_active_user, require_staff

# These tests go through the real routers -> services -> repositories with a
# prod-like session (expire_on_commit=True), the way the app runs in production.


async def seed_order(factory, status, total_price="1000", quantity=2, with_cart=False):
    """Creates two products (so item id != product id), one customer and one order."""
    async with factory() as session:
        filler = Product(name="Filler", price=Decimal(1), is_available=True)
        latte = Product(name="Latte", price=Decimal("3.50"), is_available=True, sold_count=0)
        user = User(email="a@b.c", hashed_password="x", name="User", bonus_points=0)
        session.add_all([filler, latte, user])
        await session.flush()

        order = Order(user_id=user.id, status=status, total_price=Decimal(total_price))
        session.add(order)
        await session.flush()
        session.add(OrderItem(order_id=order.id, product_id=latte.id, quantity=quantity, price_at_order=latte.price))
        if with_cart:
            session.add(Order(user_id=user.id, status=OrderStatus.CREATED, total_price=Decimal(0)))

        ids = {"user": user.id, "order": order.id, "latte": latte.id, "filler": filler.id}
        await session.commit()

    return ids


@pytest.fixture
def api(prod_like_session_factory):
    """Returns a client factory; auth is replaced by a fake user with the given id."""

    def _make(user_id, role=UserRole.ADMIN):
        class FakeUser:
            id = user_id

        FakeUser.role = role

        async def _session():
            async with prod_like_session_factory() as session:
                yield session

        app.dependency_overrides[get_db_session] = _session
        app.dependency_overrides[get_current_active_user] = lambda: FakeUser()
        app.dependency_overrides[require_staff] = lambda: FakeUser()

        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    yield _make
    app.dependency_overrides.clear()


async def test_my_orders_returns_only_non_cart_orders(prod_like_session_factory, api):
    ids = await seed_order(prod_like_session_factory, OrderStatus.PAID, with_cart=True)

    async with api(ids["user"]) as client:
        response = await client.get("/orders/")

    assert response.status_code == 200
    assert [o["id"] for o in response.json()] == [ids["order"]]


async def test_staff_sees_active_orders(prod_like_session_factory, api):
    ids = await seed_order(prod_like_session_factory, OrderStatus.PAID, with_cart=True)

    async with api(ids["user"]) as client:
        response = await client.get("/orders/staff/all")

    assert response.status_code == 200
    assert [o["id"] for o in response.json()] == [ids["order"]]


async def test_customer_can_cancel_paid_order(prod_like_session_factory, api):
    ids = await seed_order(prod_like_session_factory, OrderStatus.PAID)

    async with api(ids["user"], role=UserRole.CUSTOMER) as client:
        response = await client.post(f"/orders/{ids['order']}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


async def test_cancel_in_progress_order_is_conflict(prod_like_session_factory, api):
    ids = await seed_order(prod_like_session_factory, OrderStatus.IN_PROGRESS)

    async with api(ids["user"], role=UserRole.CUSTOMER) as client:
        response = await client.post(f"/orders/{ids['order']}/cancel")

    assert response.status_code == 409


async def test_status_change_unknown_order_is_404(prod_like_session_factory, api):
    ids = await seed_order(prod_like_session_factory, OrderStatus.PAID)

    async with api(ids["user"]) as client:
        response = await client.patch("/orders/9999/status", json={"status": "in_progress"})

    assert response.status_code == 404


async def test_status_change_paid_to_in_progress(prod_like_session_factory, api):
    ids = await seed_order(prod_like_session_factory, OrderStatus.PAID)

    async with api(ids["user"]) as client:
        response = await client.patch(f"/orders/{ids['order']}/status", json={"status": "in_progress"})

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


async def test_completing_order_credits_the_right_product_and_bonus(prod_like_session_factory, api):
    # order total 1000 (3% = 30) + 20 first-order bonus = 50 points; 2 items sold
    ids = await seed_order(prod_like_session_factory, OrderStatus.READY, total_price="1000", quantity=2)

    async with api(ids["user"]) as client:
        response = await client.patch(f"/orders/{ids['order']}/status", json={"status": "completed"})

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    async with prod_like_session_factory() as session:
        assert (await session.get(Product, ids["latte"])).sold_count == 2
        assert (await session.get(Product, ids["filler"])).sold_count == 0
        assert (await session.get(User, ids["user"])).bonus_points == 50


async def test_completing_guest_order_does_not_touch_any_user(prod_like_session_factory, api):
    async with prod_like_session_factory() as session:
        latte = Product(name="Latte", price=Decimal("3.50"), is_available=True, sold_count=0)
        user = User(email="a@b.c", hashed_password="x", name="User", bonus_points=0)
        session.add_all([latte, user])
        await session.flush()
        order = Order(user_id=None, guest_name="Guest", guest_phone="+37400000000", status=OrderStatus.READY, total_price=Decimal(100))
        session.add(order)
        await session.flush()
        session.add(OrderItem(order_id=order.id, product_id=latte.id, quantity=1, price_at_order=latte.price))
        order_id, latte_id, user_id = order.id, latte.id, user.id
        await session.commit()

    async with api(user_id) as client:
        response = await client.patch(f"/orders/{order_id}/status", json={"status": "completed"})

    assert response.status_code == 200
    async with prod_like_session_factory() as session:
        assert (await session.get(Product, latte_id)).sold_count == 1
        assert (await session.get(User, user_id)).bonus_points == 0
