from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import OrderStatus
from src.models import Order, OrderItem, Product
from src.schemas import GuestCheckoutRequest, OrderItemResponse, OrderResponse


async def get_product(session: AsyncSession, product_id: int):

    stmt = select(Product).where(Product.id == product_id)

    product = await session.scalar(stmt)

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if not product.is_available:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not available")

    return product


async def checkout_cart_total_price(order: Order, session: AsyncSession) -> tuple[Decimal, list[dict]]:
    total = Decimal(0)

    product_ids = [item.product_id for item in order.items]
    products_stmt = select(Product).where(Product.id.in_(product_ids))
    products = {p.id: p for p in (await session.scalars(products_stmt)).all()}

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

    for item in items_to_remove:
        order.items.remove(item)
        await session.delete(item)

    return total, removed_items


async def get_or_create_cart(session: AsyncSession, user_id: int) -> Order:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id, Order.status == OrderStatus.CREATED)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )

    order = await session.scalar(stmt)

    if order is not None:
        return await _heal_missing_prices(session, order)

    new_order = Order(
        user_id=user_id,
        status=OrderStatus.CREATED,
        total_price=Decimal(0),
    )

    session.add(new_order)
    await session.commit()
    await session.refresh(new_order)

    stmt = select(Order).where(Order.id == new_order.id).options(selectinload(Order.items).selectinload(OrderItem.product))

    cart = await session.scalar(stmt)

    return cart


# Self-heals cart items left with price_at_order = NULL, e.g. rows added
# to the DB before add_item_to_cart was setting that field. Without this,
# an old cart just keeps crashing GET /cart/ with `NoneType * int` forever,
# since nothing else ever fixes the stored row. Only touches the DB (and
# only re-selects) when it actually finds something to fix.
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

    stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items).selectinload(OrderItem.product))

    return await session.scalar(stmt)


async def add_item_to_cart(session: AsyncSession, user_id: int, quantity: int, product_id: int) -> Order:
    cart = await get_or_create_cart(session, user_id)
    cart_id = cart.id
    product = await get_product(session, product_id)

    existing_item = next((item for item in cart.items if item.product_id == product_id), None)

    if existing_item is not None:
        existing_item.quantity += quantity
    else:
        session.add(
            OrderItem(
                order_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                price_at_order=product.price,
            )
        )

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

    cart.items.remove(item)
    await session.delete(item)
    await session.commit()

    return await recalculate_cart_total(session, cart_id)


# Takes an order_id (not an Order instance) on purpose: every caller here
# has just called session.commit(), which expires ORM objects still held
# in that session (expire_on_commit=True) - accessing order.id on an
# expired instance triggers a lazy-load outside of an awaited call and
# raises MissingGreenlet. An id is a plain int and can't go stale.
async def recalculate_cart_total(session: AsyncSession, order_id: int) -> Order:
    stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items).selectinload(OrderItem.product))
    order = await session.scalar(stmt)

    order.total_price = sum(
        (item.price_at_order * item.quantity for item in order.items),
        start=Decimal(0),
    )

    await session.commit()
    await session.refresh(order, attribute_names=["items"])

    return order


async def checkout_cart_for_user(session: AsyncSession, user_id: int) -> Order:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id, Order.status == OrderStatus.CREATED)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .with_for_update()
    )
    order = await session.scalar(stmt)

    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    return await checkout_cart(session, order)


async def checkout_cart(session: AsyncSession, order: Order) -> Order:
    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    total_price, removed_items = await checkout_cart_total_price(order, session)

    if removed_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Some items are no longer available.",
                "removed_items": removed_items,
            },
        )

    order.total_price = total_price
    order.status = OrderStatus.PAID

    order_id = order.id

    await session.commit()

    stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items).selectinload(OrderItem.product))

    order = await session.scalar(stmt)

    return order


async def guest_checkout_service(
    session: AsyncSession,
    payload: GuestCheckoutRequest,
    guest_session_id: str,
):
    order = Order(
        user_id=None,
        guest_name=payload.contact.name,
        guest_phone=payload.contact.phone,
        guest_email=payload.contact.email,
        status=OrderStatus.CREATED,
        total_price=Decimal(0),
    )

    session.add(order)
    await session.flush()

    for item in payload.items:
        product = await get_product(session, item.product_id)

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            price_at_order=product.price,
        )

        session.add(order_item)

    stmt = select(Order).where(Order.id == order.id).options(selectinload(Order.items).selectinload(OrderItem.product))

    order = await session.scalar(stmt)

    order = await checkout_cart(session, order)

    await session.refresh(
        order,
        attribute_names=["items"],
    )

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
