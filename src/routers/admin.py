import math
import uuid
from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import OrderStatus, UserRole, db_session
from src.models import Order, User
from src.schemas import AdminUserResponse, AdminUserStatsResponse, Page, UserResetPassword, UserRoleUpdate
from src.services import hash_password
from src.validators import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


# Admin Dashboard


@router.get("/dashboard")
async def admin_dashboard(current_admin: User = Depends(require_admin)):
    return {
        "message": f"Welcome, {current_admin.name}. This is the admin dashboard.",
    }


# User Management


SORTABLE_FIELDS = {"id", "created_at", "orders_count", "total_spent", "reviews_count"}


@router.get("/users", response_model=Page[AdminUserResponse])
async def list_users(
    search: str | None = Query(None, description="Matches user ID, email or name"),
    role: UserRole | None = Query(None),
    is_active: bool | None = Query(None),
    is_email_verified: bool | None = Query(None),
    has_orders: bool | None = Query(None),
    has_reviews: bool | None = Query(None),
    sort_by: str = Query("id", description="One of: " + ", ".join(sorted(SORTABLE_FIELDS))),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(db_session),
    _: User = Depends(require_admin),
):
    if sort_by not in SORTABLE_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"sort_by must be one of: {', '.join(sorted(SORTABLE_FIELDS))}",
        )

    result = await session.execute(select(User).options(selectinload(User.orders), selectinload(User.reviews)))
    users = list(result.scalars().all())

    if search:
        needle = search.strip().lower()
        users = [user for user in users if needle == str(user.id) or needle in user.email.lower() or needle in user.name.lower()]
    if role is not None:
        users = [user for user in users if user.role == role]
    if is_active is not None:
        users = [user for user in users if user.is_active == is_active]
    if is_email_verified is not None:
        users = [user for user in users if user.is_email_verified == is_email_verified]
    if has_orders is not None:
        users = [user for user in users if bool(user.orders) == has_orders]
    if has_reviews is not None:
        users = [user for user in users if bool(user.reviews) == has_reviews]

    money_statuses = {OrderStatus.PAID, OrderStatus.IN_PROGRESS, OrderStatus.READY, OrderStatus.COMPLETED}

    def sort_key(user: User):
        if sort_by == "created_at":
            return user.created_at
        if sort_by == "orders_count":
            return len(user.orders)
        if sort_by == "total_spent":
            return sum(
                (order.total_price for order in user.orders if order.status in money_statuses),
                Decimal("0.00"),
            )
        if sort_by == "reviews_count":
            return len(user.reviews)
        return user.id

    users.sort(key=sort_key, reverse=(sort_order == "desc"))

    total = len(users)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    page_items = users[start : start + page_size]

    return Page(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
async def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    session: AsyncSession = Depends(db_session),
    current_admin: User = Depends(require_admin),
):
    stmt = select(User).where(User.id == user_id)
    user = await session.scalar(stmt)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_admin.id and payload.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot demote yourself from the admin role",
        )

    user.role = payload.role
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password", response_model=UserResetPassword)
async def reset_user_password(
    user_id: int,
    session: AsyncSession = Depends(db_session),
    _: User = Depends(require_admin),
):
    stmt = select(User).where(User.id == user_id)
    user = await session.scalar(stmt)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    temporary_password = uuid.uuid4().hex
    user.hashed_password = hash_password(temporary_password).decode("utf-8")
    user.must_change_password = True

    await session.commit()
    return {"password": temporary_password}


@router.get("/users/{user_id}/stats", response_model=AdminUserStatsResponse)
async def get_user_stats(
    user_id: int,
    session: AsyncSession = Depends(db_session),
    _: User = Depends(require_admin),
):
    """Powers the "Подробнее" popup on the admin Users page.

    Policy:
      - CREATED orders are still carts/drafts, not real orders yet, so
        they're excluded everywhere (orders_count and total_spent).
      - CANCELLED orders did happen, so they count towards orders_count,
        but not towards total_spent since nothing was actually paid.
      - PAID / IN_PROGRESS / READY / COMPLETED count towards both.
    """
    user = await session.scalar(
        select(User)
        .options(
            selectinload(User.orders),
            selectinload(User.reviews),
        )
        .where(User.id == user_id)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    orders_by_status: dict[str, list[Order]] = defaultdict(list)
    for order in user.orders:
        if order.status == OrderStatus.CREATED:
            continue
        orders_by_status[order.status.value].append(order)

    orders_count = sum(len(orders) for orders in orders_by_status.values())

    money_statuses = {OrderStatus.PAID, OrderStatus.IN_PROGRESS, OrderStatus.READY, OrderStatus.COMPLETED}
    orders_breakdown = {status_key: sum((order.total_price for order in orders), Decimal("0.00")) for status_key, orders in orders_by_status.items()}
    total_spent = sum(
        (total for status_key, total in orders_breakdown.items() if status_key in {s.value for s in money_statuses}),
        Decimal("0.00"),
    )

    return AdminUserStatsResponse(
        orders=orders_breakdown,
        total_spent=total_spent,
        reviews=user.reviews,
        reviews_count=len(user.reviews),
        orders_count=orders_count,
    )
