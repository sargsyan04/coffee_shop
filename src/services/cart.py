from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import OrderStatus
from src.models import Order, Product
from src.repositories import (
    add_new_item_to_cart,
    create_cart,
    create_guest_order,
    delete_order_items,
    get_cart_by_user_id,
    get_order_by_id,
    get_product_by_id,
    get_products_list,
)
from src.schemas import GuestCheckoutRequest, OrderItemResponse, OrderResponse


async def checkout_cart_total_price(order: Order, session: AsyncSession) -> tuple[Decimal, list[dict]]:
    total = Decimal(0)

    product_ids = [item.product_id for item in order.items]

    products = await get_products_list(session, product_ids)

    removed_items = []
    items_to_remove = []

    for item in order.items:
        product = products.get(item.product_id)

        if product is None:
            removed_items.append(
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else "Unknown product",
                    "reason": "not_found",
                }
            )
            items_to_remove.append(item)
            continue

        if not product.is_available:
            removed_items.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "reason": "unavailable",
                }
            )
            items_to_remove.append(item)
            continue

        item.price_at_order = product.price
        total += product.price * item.quantity

    await delete_order_items(session, order, items=items_to_remove)

    return total, removed_items


async def get_available_product(session: AsyncSession, product_id: int) -> Product:
    product = await get_product_by_id(session, product_id)

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if not product.is_available:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not available")

    return product


async def get_or_create_cart(session: AsyncSession, user_id: int) -> Order:
    cart = await get_cart_by_user_id(session, user_id)

    if cart is not None:
        return await _heal_missing_prices(session, cart)

    new_cart = await create_cart(session, user_id)
    cart_id = new_cart.id

    await session.commit()

    return await get_order_by_id(session, cart_id, user_id)


# Self-heals cart items left with price_at_order = NULL, e.g. rows added
# to the DB before add_item_to_cart was setting that field. Without this,
# an old cart just keeps crashing GET /cart/ with `NoneType * int` forever,
# since nothing else ever fixes the stored row.
async def _heal_missing_prices(session: AsyncSession, order: Order) -> Order:
    order_id = order.id
    dirty = False

    for item in order.items:
        if item.price_at_order is None and item.product is not None:
            item.price_at_order = item.product.price
            dirty = True

    if not dirty:
        return order

    await session.commit()

    return await get_order_by_id(session, order_id)


async def add_item_to_cart(session: AsyncSession, user_id: int, quantity: int, product_id: int) -> Order:
    cart = await get_or_create_cart(session, user_id)
    cart_id = cart.id
    product = await get_available_product(session, product_id)

    existing_item = next((item for item in cart.items if item.product_id == product_id), None)

    if existing_item is not None:
        existing_item.quantity += quantity
    else:
        await add_new_item_to_cart(session, cart, product, quantity)

    await session.commit()

    return await recalculate_cart_total(session, cart_id)


async def update_item_quantity(session: AsyncSession, user_id: int, item_id: int, quantity: int) -> Order:
    cart = await get_or_create_cart(session, user_id)
    cart_id = cart.id

    item = next((i for i in cart.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")

    item.quantity = quantity

    await session.commit()

    return await recalculate_cart_total(session, cart_id)


async def remove_item_from_cart(session: AsyncSession, user_id: int, item_id: int) -> Order:
    cart = await get_or_create_cart(session, user_id)
    cart_id = cart.id

    item = next((i for i in cart.items if i.id == item_id), None)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")

    await delete_order_items(session, cart, item=item)

    await session.commit()

    return await recalculate_cart_total(session, cart_id)


async def recalculate_cart_total(session: AsyncSession, order_id: int) -> Order:
    order = await get_order_by_id(session, order_id)

    order.total_price = sum(
        (item.price_at_order * item.quantity for item in order.items),
        start=Decimal(0),
    )

    await session.commit()

    return await get_order_by_id(session, order_id, refresh=True)


async def checkout_cart_for_user(session: AsyncSession, user_id: int) -> Order:
    order = await get_cart_by_user_id(session, user_id, for_update=True)

    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    return await checkout_cart(session, order)


async def checkout_cart(session: AsyncSession, order: Order) -> Order:
    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    order_id = order.id

    total_price, removed_items = await checkout_cart_total_price(order, session)

    if removed_items:
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Some items are no longer available.",
                "removed_items": removed_items,
            },
        )

    order.total_price = total_price
    order.status = OrderStatus.PAID

    await session.commit()

    order = await get_order_by_id(session, order_id)

    return order


async def guest_checkout_service(session: AsyncSession, payload: GuestCheckoutRequest, guest_session_id: str):
    order = await create_guest_order(
        session,
        payload.contact.name,
        payload.contact.phone,
        payload.contact.email,
    )
    order_id = order.id

    for item in payload.items:
        product = await get_available_product(session, item.product_id)

        await add_new_item_to_cart(session, order, product, item.quantity)

    order = await get_order_by_id(session, order_id)

    order = await checkout_cart(session, order)

    return build_order_response(order)


def build_order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        status=order.status,
        total_price=order.total_price,
        created_at=order.created_at,
        removed_items=[],
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=item.price_at_order,
                line_total=item.price_at_order * item.quantity,
            )
            for item in order.items
        ],
    )
