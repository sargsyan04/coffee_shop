from decimal import Decimal

import pytest

from src.core.enums import OrderStatus
from src.models import Product, User
from src.services import (
    add_item_to_cart,
    build_order_response,
    checkout_cart_for_user,
    remove_item_from_cart,
    update_item_quantity,
)


@pytest.fixture
async def user_and_product_ids(prod_like_session_factory):
    async with prod_like_session_factory() as session:
        user = User(email="cart@example.com", hashed_password="x", name="Cart User")
        product = Product(name="Latte", price=Decimal("3.50"), is_available=True)
        session.add_all([user, product])
        await session.flush()
        ids = (user.id, product.id)
        await session.commit()
    return ids


async def test_add_item_returns_fully_loaded_cart(prod_like_session_factory, user_and_product_ids):
    user_id, product_id = user_and_product_ids

    async with prod_like_session_factory() as session:
        cart = await add_item_to_cart(session, user_id, 2, product_id)
        response = build_order_response(cart)  # used to raise MissingGreenlet

    assert response.status == OrderStatus.CREATED
    assert response.total_price == Decimal("7.00")
    assert response.items[0].quantity == 2


async def test_update_and_remove_item(prod_like_session_factory, user_and_product_ids):
    user_id, product_id = user_and_product_ids

    async with prod_like_session_factory() as session:
        cart = await add_item_to_cart(session, user_id, 1, product_id)
        item_id = cart.items[0].id

    async with prod_like_session_factory() as session:
        cart = await update_item_quantity(session, user_id, item_id, 4)
        assert build_order_response(cart).total_price == Decimal("14.00")

    async with prod_like_session_factory() as session:
        cart = await remove_item_from_cart(session, user_id, item_id)
        response = build_order_response(cart)

    assert response.items == []
    assert response.total_price == Decimal("0.00")


async def test_full_flow_add_then_checkout(prod_like_session_factory, user_and_product_ids):
    user_id, product_id = user_and_product_ids

    async with prod_like_session_factory() as session:
        await add_item_to_cart(session, user_id, 3, product_id)

    async with prod_like_session_factory() as session:
        order = await checkout_cart_for_user(session, user_id)
        response = build_order_response(order)

    assert response.status == OrderStatus.PAID
    assert response.total_price == Decimal("10.50")


async def test_guest_checkout_returns_fully_loaded_order(prod_like_session_factory, user_and_product_ids):
    from src.schemas import GuestCheckoutRequest
    from src.services import guest_checkout_service

    _, product_id = user_and_product_ids
    payload = GuestCheckoutRequest(
        items=[{"product_id": product_id, "quantity": 2}],
        contact={"name": "Guest", "phone": "+37400000000"},
    )

    async with prod_like_session_factory() as session:
        response = await guest_checkout_service(session, payload, "guest-session")

    assert response.status == OrderStatus.PAID
    assert response.total_price == Decimal("7.00")
    assert response.items[0].product_name == "Latte"
