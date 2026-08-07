import pytest
from fastapi import HTTPException

from src.core import OrderStatus, UserRole
from src.validators.order import get_order_or_404, validate_status_transition


@pytest.mark.parametrize(
    "current_status, new_status",
    [
        (OrderStatus.CREATED, OrderStatus.PAID),
        (OrderStatus.CREATED, OrderStatus.CANCELLED),
        (OrderStatus.PAID, OrderStatus.IN_PROGRESS),
        (OrderStatus.PAID, OrderStatus.CANCELLED),
        (OrderStatus.IN_PROGRESS, OrderStatus.READY),
        (OrderStatus.READY, OrderStatus.COMPLETED),
    ],
)
def test_allowed_status_transitions(current_status, new_status):
    # should not raise
    validate_status_transition(current_status, new_status)


@pytest.mark.parametrize(
    "current_status, new_status",
    [
        (OrderStatus.CREATED, OrderStatus.READY),  # skipping steps
        (OrderStatus.CREATED, OrderStatus.COMPLETED),
        (OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED),  # too late to cancel
        (OrderStatus.COMPLETED, OrderStatus.CREATED),  # completed orders are final
        (OrderStatus.COMPLETED, OrderStatus.CANCELLED),
        (OrderStatus.CANCELLED, OrderStatus.CREATED),  # cancelled orders are final too
    ],
)
def test_forbidden_status_transitions(current_status, new_status):
    with pytest.raises(HTTPException) as exc_info:
        validate_status_transition(current_status, new_status)

    assert exc_info.value.status_code == 409


async def test_customer_can_fetch_own_order(db_session, user_factory, order_factory):
    user = await user_factory()
    order = await order_factory(user)

    found = await get_order_or_404(db_session, order.id, user)

    assert found.id == order.id


async def test_customer_cannot_fetch_someone_elses_order(db_session, user_factory, order_factory):
    owner = await user_factory()
    other_customer = await user_factory()
    order = await order_factory(owner)

    with pytest.raises(HTTPException) as exc_info:
        await get_order_or_404(db_session, order.id, other_customer)

    assert exc_info.value.status_code == 404


async def test_staff_can_fetch_any_order(db_session, user_factory, order_factory):
    owner = await user_factory()
    barista = await user_factory(role=UserRole.BARISTA)
    order = await order_factory(owner)

    found = await get_order_or_404(db_session, order.id, barista)

    assert found.id == order.id


async def test_missing_order_raises_404(db_session, user_factory):
    user = await user_factory()

    with pytest.raises(HTTPException) as exc_info:
        await get_order_or_404(db_session, 999999, user)

    assert exc_info.value.status_code == 404
