from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import User, Order
from src.core import db_session, OrderStatus
from src.validators import get_current_active_user

from src.schemas import CartItemAdd, CartItemUpdate, OrderResponse
# from src.services import (
#     get_or_create_cart,
#     add_item_to_cart,
#     update_item_quantity,
#     remove_item_from_cart,
#     checkout_cart,
# )

router = APIRouter(prefix="/cart", tags=["Cart"])


# ============================================================
# --> View Current Cart <--
# ============================================================


@router.get("/", response_model=OrderResponse)
async def get_cart(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: call get_or_create_cart(session, current_user.id) instead of a raw query
    # TODO: build the OrderResponse manually (product_name/unit_price/line_total
    #       don't exist as plain attributes on OrderItem - see schemas/order.py)
    user_id = current_user.id

    stmt = select(Order).where(Order.user_id == user_id)

    cart = await session.scalar(stmt)

    return cart


# ============================================================
# --> Add / Update / Remove Items <--
# ============================================================


@router.post("/items", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    payload: CartItemAdd,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: call add_item_to_cart(session, current_user.id, payload.product_id, payload.quantity)
    # TODO: return the built OrderResponse
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")


@router.patch("/items/{item_id}", response_model=OrderResponse)
async def update_item(
    item_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: call update_item_quantity(session, current_user.id, item_id, payload.quantity)
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")


@router.delete("/items/{item_id}", response_model=OrderResponse)
async def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: call remove_item_from_cart(session, current_user.id, item_id)
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")


# ============================================================
# --> Checkout <--
# ============================================================


@router.post("/checkout", response_model=OrderResponse)
async def checkout(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    stmt = (
        select(Order)
        .where(Order.user_id == current_user.id, Order.status == OrderStatus.CREATED)
        .options(selectinload(Order.items))
        # TODO: also .with_for_update() to protect against a double checkout race
    )
    order = await session.scalar(stmt)

    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    # TODO: move the checks/logic below into services.checkout_cart(session, order)
    #       instead of inlining business logic in the router
    if not order.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    order.total_price = await checkout_cart_total_price(order, session)
    order.status = OrderStatus.PAID

    await session.commit()
    await session.refresh(order)

    return order