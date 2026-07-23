from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Order, Product, OrderItem
from src.core import OrderStatus


async def checkout_cart_total_price(order: Order, session: AsyncSession) -> tuple[Decimal, list[dict]]:
    total = Decimal("0")

    product_ids = [item.product_id for item in order.items]
    products_stmt = select(Product).where(Product.id.in_(product_ids))
    products = {p.id: p for p in (await session.scalars(products_stmt)).all()}

    removed_items = []
    items_to_remove = []

    for item in order.items:
        product = products.get(item.product_id)

        if product is None:
            removed_items.append({
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "Unknown product",
                "reason": "not_found",
            })
            items_to_remove.append(item)
            continue

        if not product.is_available:
            removed_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "reason": "unavailable",
            })
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
        return order

    new_order = Order(
        user_id=user_id,
        status=OrderStatus.CREATED,
        total_price=Decimal("0"),
    )

    session.add(new_order)
    await session.commit()
    await session.refresh(new_order)

    stmt = (
        select(Order)
        .where(Order.id == new_order.id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )

    return await session.scalar(stmt)



async def add_item_to_cart(session: AsyncSession, user_id: int, product_id: int, quantity: int) -> Order:
    """
    TODO:
    - get_or_create_cart(session, user_id)
    - load Product by product_id, 404 if missing, 409 if not is_available
    - if product already in cart items -> increase quantity
      else -> create new OrderItem with price_at_order = product.price
    - call recalculate_cart_total and commit
    """
    pass


async def update_item_quantity(session: AsyncSession, user_id: int, item_id: int, quantity: int) -> Order:
    """
    TODO:
    - load current user's cart, find item_id in it, 404 if not found/not owned
    - update quantity, recalculate_cart_total, commit
    """
    pass


async def remove_item_from_cart(session: AsyncSession, user_id: int, item_id: int) -> Order:
    """
    TODO:
    - load current user's cart, find item_id in it, 404 if not found/not owned
    - delete the item, recalculate_cart_total, commit
    """
    pass


async def recalculate_cart_total(session: AsyncSession, order: Order) -> Order:
    """
    TODO:
    - sum item.price_at_order * item.quantity across order.items
    - assign to order.total_price
    - commit and return the refreshed order
    """
    pass


async def checkout_cart(session: AsyncSession, order: Order) -> Order:
    """
    TODO:
    - 400 if order.items is empty
    - recalc total via checkout_cart_total_price (reject if any product unavailable)
    - set status = PAID, commit
    - TODO: award loyalty points (loyalty_service)
    - TODO: decrement ingredient stock (inventory_service)
    - TODO: notify staff over WebSocket about the new order
    """
    pass