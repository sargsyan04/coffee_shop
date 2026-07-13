from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.core import db_session
from src.validators import get_current_active_user, require_staff
from src.schemas import OrderResponse, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


# ============================================================
# --> Customer-Facing Endpoints <--
# ============================================================

@router.get("/")
async def get_my_orders(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: return all orders for current_user, excluding the current CREATED cart
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{order_id}")
async def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: fetch order, verify it belongs to current_user (unless staff)
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: verify ownership, verify status is CREATED or PAID, set CANCELLED
    raise HTTPException(status_code=501, detail="Not implemented yet")


# ============================================================
# --> Staff-Facing Endpoints (baristas & admins) <--
# ============================================================

@router.get("/staff/all")
async def get_all_active_orders(
    current_staff: User = Depends(require_staff),
    session: AsyncSession = Depends(db_session),
):
    # TODO: return orders with status in (PAID, IN_PROGRESS, READY), for staff to manage
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    # payload: OrderStatusUpdate,
    current_staff: User = Depends(require_staff),
    session: AsyncSession = Depends(db_session),
):
    # TODO: validate status transition, update status,
    #       on transition to COMPLETED: increment Product.sold_count and award bonus_points
    raise HTTPException(status_code=501, detail="Not implemented yet")