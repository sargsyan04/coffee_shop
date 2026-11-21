from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import OrderStatus
from src.models import Order, OrderItem, Product


async def get_cart_by_user_id(session: AsyncSession, user_id: int, for_update: bool = False) -> Order | None:
    stmt = (
        select(Order)
        .where(
            Order.user_id == user_id,
            Order.status == OrderStatus.CREATED,
        )
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )

    if for_update:
        stmt = stmt.with_for_update()

    return await session.scalar(stmt)


async def get_order_by_id(
    session: AsyncSession,
    order_id: int,
    user_id: int | None = None,
    refresh: bool = False,
) -> Order | None:
    conditions = [Order.id == order_id]

    if user_id is not None:
        conditions.append(Order.user_id == user_id)

    stmt = select(Order).where(*conditions).options(selectinload(Order.items).selectinload(OrderItem.product))

    if refresh:
        # Overwrite objects already sitting in the session with the fresh DB state
        stmt = stmt.execution_options(populate_existing=True)

    return await session.scalar(stmt)


async def create_cart(session: AsyncSession, user_id: int) -> Order:
    new_cart = Order(
        user_id=user_id,
        status=OrderStatus.CREATED,
        total_price=Decimal(0),
    )

    session.add(new_cart)
    await session.flush()

    return new_cart


async def create_guest_order(session: AsyncSession, name: str, phone: str, email: str | None) -> Order:
    order = Order(
        user_id=None,
        guest_name=name,
        guest_phone=phone,
        guest_email=email,
        status=OrderStatus.CREATED,
        total_price=Decimal(0),
    )

    session.add(order)
    await session.flush()

    return order


async def add_new_item_to_cart(session: AsyncSession, cart: Order, product: Product, quantity: int) -> None:
    session.add(
        OrderItem(
            order_id=cart.id,
            product_id=product.id,
            quantity=quantity,
            price_at_order=product.price,
        )
    )

    await session.flush()


async def delete_order_items(
    session: AsyncSession,
    order: Order,
    item: OrderItem | None = None,
    items: list[OrderItem] | None = None,
) -> None:
    if item is None and items is None:
        raise ValueError("Please select an item to delete")

    items_to_delete = items if items is not None else [item]

    for order_item in items_to_delete:
        order.items.remove(order_item)
        await session.delete(order_item)

    await session.flush()


async def update_order_status(session: AsyncSession, order: Order, status: OrderStatus) -> None:
    order.status = status

    await session.flush()
