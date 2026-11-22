from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import UserRole
from src.core.enums import OrderStatus
from src.models import Order, User
from src.repositories import get_order_by_id

# Order Status Transitions

ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED},
    OrderStatus.IN_PROGRESS: {OrderStatus.READY},
    OrderStatus.READY: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


# Order Lookup


async def get_order_or_404(
    session: AsyncSession,
    order_id: int,
    current_user: User,
) -> Order:

    if current_user.role not in (UserRole.BARISTA, UserRole.ADMIN):
        order = await get_order_by_id(session, order_id, current_user.id)
    else:
        order = await get_order_by_id(
            session,
            order_id,
        )

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return order


def validate_status_transition(current_status: OrderStatus, new_status: OrderStatus) -> None:
    """Raises 409 if moving from current_status to new_status isn't allowed."""

    if new_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition order from {current_status} to {new_status}",
        )
