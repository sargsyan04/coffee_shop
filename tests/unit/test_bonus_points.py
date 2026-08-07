from decimal import Decimal

import pytest

from src.core import OrderStatus
from src.services.bonus_points import _get_base_rate, calculate_bonus_points


@pytest.mark.parametrize(
    "order_total, expected_rate",
    [
        (0, 0.03),
        (2_999, 0.03),
        (3_000, 0.05),
        (6_999, 0.05),
        (7_000, 0.08),
        (50_000, 0.08),
    ],
)
def test_get_base_rate(order_total, expected_rate):
    assert _get_base_rate(order_total) == expected_rate


async def test_calculate_bonus_points(db_session, user_factory, order_factory):
    user = await user_factory()
    order = await order_factory(user, total_price=Decimal("5000.00"))

    points = await calculate_bonus_points(db_session, order, total_items=2)

    assert points == 270


async def test_bulk_bonus_applies(db_session, user_factory, order_factory):
    # already has a completed order, so the +20 first-order bonus is out of the way
    # and we're only checking the bulk rate here
    user = await user_factory()
    await order_factory(user, total_price=Decimal("1000.00"), status=OrderStatus.COMPLETED)

    order = await order_factory(user, total_price=Decimal("1000.00"))
    points = await calculate_bonus_points(db_session, order, total_items=5)

    # base rate for 1000 is 3%, plus 2% bulk bonus = 5% of 1000
    assert points == 50


async def test_bulk_bonus_combines_with_top_tier(db_session, user_factory, order_factory):
    user = await user_factory()
    await order_factory(user, status=OrderStatus.COMPLETED)

    order = await order_factory(user, total_price=Decimal("10000.00"))
    points = await calculate_bonus_points(db_session, order, total_items=6)

    # top tier 8% + 2% bulk = 10% of 10000
    assert points == 1000


@pytest.mark.parametrize(
    "total_items, expected_points",
    [
        (4, 30),  # below threshold - base rate only (3% of 1000)
        (5, 50),  # right at threshold - bulk bonus kicks in (5% of 1000)
    ],
)
async def test_bulk_bonus_threshold(db_session, user_factory, order_factory, total_items, expected_points):
    user = await user_factory()
    await order_factory(user, status=OrderStatus.COMPLETED)

    order = await order_factory(user, total_price=Decimal("1000.00"))
    points = await calculate_bonus_points(db_session, order, total_items=total_items)

    assert points == expected_points


async def test_no_first_order_bonus_for_repeat_customer(db_session, user_factory, order_factory):
    user = await user_factory()
    await order_factory(user, status=OrderStatus.COMPLETED)

    order = await order_factory(user, total_price=Decimal("5000.00"))
    points = await calculate_bonus_points(db_session, order, total_items=2)

    # same numbers as test_calculate_bonus_points, just without the +20 - this
    # user already has a completed order behind them
    assert points == 250


async def test_cancelled_order_does_not_count_as_previous(db_session, user_factory, order_factory):
    user = await user_factory()
    await order_factory(user, status=OrderStatus.CANCELLED)

    order = await order_factory(user, total_price=Decimal("5000.00"))
    points = await calculate_bonus_points(db_session, order, total_items=2)

    # a cancelled order shouldn't count as a "previous completed order" -
    # the first-order bonus still applies here
    assert points == 270
