from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import db_session
from src.core.enums import OrderStatus
from src.models import User
from src.schemas import OrderResponse, OrderStatusUpdate
from src.services import (
    build_order_response,
    get_order,
    order_status_change,
    orders_for_staff,
    user_orders_list,
)
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
    orders = await user_orders_list(session, current_user)

    return [build_order_response(order) for order in orders]


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

    order = await order_status_change(session, order, OrderStatus.CANCELLED)

    return build_order_response(order)


# Staff-Facing Endpoints (baristas & admins)


@router.get("/staff/all", response_model=list[OrderResponse])
async def get_all_active_orders(
    _: User = Depends(require_staff),
    session: AsyncSession = Depends(db_session),
):
    orders = await orders_for_staff(session)

    return [build_order_response(order) for order in orders]


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    _: User = Depends(require_staff),
    session: AsyncSession = Depends(db_session),
):
    order = await get_order(session, order_id)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    validate_status_transition(order.status, payload.status)

    order = await order_status_change(session, order, payload.status)

    return build_order_response(order)
