from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import db_session
from src.models import User
from src.schemas import CartItemAdd, CartItemUpdate, OrderResponse
from src.services import (
    add_item_to_cart,
    build_order_response,
    checkout_cart_for_user,
    get_or_create_cart,
    remove_item_from_cart,
    update_item_quantity,
)
from src.validators import get_current_active_user

router = APIRouter(prefix="/cart", tags=["Cart"])


# ============================================================
# --> View Current Cart <--
# ============================================================


@router.get("/", response_model=OrderResponse)
async def get_cart(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    cart = await get_or_create_cart(session, current_user.id)
    return build_order_response(cart)


@router.post("/items", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    payload: CartItemAdd,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    cart = await add_item_to_cart(session, current_user.id, payload.quantity, payload.product_id)

    return build_order_response(cart)


@router.patch("/items/{item_id}", response_model=OrderResponse)
async def update_item(
    item_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    cart = await update_item_quantity(session, current_user.id, item_id, payload.quantity)

    return build_order_response(cart)


@router.delete("/items/{item_id}", response_model=OrderResponse)
async def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    cart = await remove_item_from_cart(session, current_user.id, item_id)

    return build_order_response(cart)


@router.post("/checkout", response_model=OrderResponse)
async def checkout(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    order = await checkout_cart_for_user(session, current_user.id)

    return build_order_response(order)
