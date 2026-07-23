from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import OrderStatus
from src.models import Order

# ============================================================
# --> Bonus Points Calculation <--
# ============================================================

# --> Base rate scales with order total — bigger orders earn a better rate <--
BASE_RATE_TIERS: list[tuple[int, float]] = [
    (7_000, 0.08),  # 7 000+ ֏           -> 8%
    (3_000, 0.05),  # 3 000 - 6 999 ֏    -> 5%
    (0, 0.03),  # 0 - 2 999 ֏        -> 3%
]

# --> Extra rate on top of the base, when the order has enough items <--
BULK_ITEM_THRESHOLD = 5  # total quantity across all items in the order
BULK_ITEM_BONUS_RATE = 0.02  # +2% on top of the base rate

# --> One-time flat bonus for a customer's very first completed order <--
FIRST_ORDER_BONUS_POINTS = 20


def _get_base_rate(order_total: float) -> float:
    for threshold, rate in BASE_RATE_TIERS:
        if order_total >= threshold:
            return rate
    return BASE_RATE_TIERS[-1][1]


async def calculate_bonus_points(session: AsyncSession, order: Order, total_items: int) -> int:
    """Computes how many bonus points a completed order earns.

    order_total       — the order's final price, used for the tiered base rate.
    total_items        — total quantity across all order items (sum of item.quantity),
                          used to check the bulk-order bonus.
    """

    rate = _get_base_rate(order.total_price)

    # --> Bulk bonus: enough items in a single order earns an extra rate <--
    if total_items >= BULK_ITEM_THRESHOLD:
        rate += BULK_ITEM_BONUS_RATE

    points = int(order.total_price * rate)

    # --> First-order bonus: check if this is the customer's first ever
    #     COMPLETED order (this one doesn't count yet, since its status
    #     hasn't been committed as COMPLETED at the time of this check) <--
    stmt = select(Order).where(
        Order.user_id == order.user_id,
        Order.status == OrderStatus.COMPLETED,
    )
    has_previous_completed_order = (await session.scalar(stmt)) is not None

    if not has_previous_completed_order:
        points += FIRST_ORDER_BONUS_POINTS

    return points
