from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import UserRole
from src.core.enums import OrderStatus
from src.models import Order, User

# ============================================================
# --> Order Lookup <--
# ============================================================


async def get_order_or_404(
    session: AsyncSession,
    order_id: int,
    current_user: User,
) -> Order:
    """Fetches an order by id, scoped to the current user unless they're staff.
    Raises 404 if the order doesn't exist or doesn't belong to the caller."""

    stmt = select(Order).where(Order.id == order_id)

    if current_user.role not in (UserRole.BARISTA, UserRole.ADMIN):
        stmt = stmt.where(Order.user_id == current_user.id)

    order = await session.scalar(stmt)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return order


# ============================================================
# --> Order Status Transitions <--
# ============================================================

# --> Allowed status transitions — staff can only move an order forward
#     along this path, or cancel it while it's still early enough <--
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED},
    OrderStatus.IN_PROGRESS: {OrderStatus.READY},
    OrderStatus.READY: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


def validate_status_transition(current_status: OrderStatus, new_status: OrderStatus) -> None:
    """Raises 409 if moving from current_status to new_status isn't allowed."""

    if new_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition order from {current_status} to {new_status}",
        )
