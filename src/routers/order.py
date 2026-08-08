from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import db_session
from src.core.enums import OrderStatus
from src.models import Order, OrderItem, Product, User
from src.schemas import OrderResponse, OrderStatusUpdate
from src.services import build_order_response, calculate_bonus_points
from src.validators import (
    get_current_active_user,
    get_order_or_404,
    require_staff,
    validate_status_transition,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# Customer-Facing Endpoints


@router.get("/", response_model=list[OrderResponse])
async def get_my_orders(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # Excludes the current CREATED cart — that's not a placed order yet
    stmt = (
        select(Order)
        .where(
            Order.user_id == current_user.id,
            Order.status != OrderStatus.CREATED,
        )
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.desc())
    )

    orders = await session.scalars(stmt)
    return [build_order_response(order) for order in orders.all()]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    order = await get_order_or_404(session, order_id, current_user)
    return build_order_response(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    order = await get_order_or_404(session, order_id, current_user)

    validate_status_transition(order.status, OrderStatus.CANCELLED)

    order.status = OrderStatus.CANCELLED

    await session.commit()

    # commit() expires `order`, so re-select by the plain order_id int
    # (not by re-calling get_order_or_404, which would touch the now-also
    # -expired current_user) with items/product eager-loaded for the response
    stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items).selectinload(OrderItem.product))
    order = await session.scalar(stmt)

    return build_order_response(order)


# Staff-Facing Endpoints (baristas & admins)


@router.get("/staff/all", response_model=list[OrderResponse])
async def get_all_active_orders(
    _: User = Depends(require_staff),
    session: AsyncSession = Depends(db_session),
):
    # Only orders staff currently needs to act on:
    # paid (ready to start), in progress, or ready for pickup
    stmt = (
        select(Order)
        .where(Order.status.in_((OrderStatus.PAID, OrderStatus.IN_PROGRESS, OrderStatus.READY)))
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.asc())
    )

    orders = await session.scalars(stmt)
    return [build_order_response(order) for order in orders.all()]


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    _: User = Depends(require_staff),
    session: AsyncSession = Depends(db_session),
):
    stmt = select(Order).where(Order.id == order_id)
    order = await session.scalar(stmt)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    validate_status_transition(order.status, payload.status)

    # Must run BEFORE we flip the status to COMPLETED below — the
    # first-order bonus check needs to see this order as not-yet-completed
    if payload.status == OrderStatus.COMPLETED:
        items_stmt = select(OrderItem).where(OrderItem.order_id == order.id)
        items = (await session.scalars(items_stmt)).all()
        total_items = sum(item.quantity for item in items)

        # Credit sold_count for every product in the order
        for item in items:
            product = await session.get(Product, item.product_id)
            if product:
                product.sold_count += item.quantity

        # Award bonus points to the customer
        points = await calculate_bonus_points(session, order, total_items)

        customer = await session.get(User, order.user_id)
        if customer:
            customer.bonus_points += points

    order.status = payload.status

    await session.commit()

    # same reason as in cancel_order: re-select by order_id with items
    # eager-loaded instead of session.refresh(order), which doesn't load
    # relationships and would leave `order` expired for build_order_response
    stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items).selectinload(OrderItem.product))
    order = await session.scalar(stmt)

    return build_order_response(order)
