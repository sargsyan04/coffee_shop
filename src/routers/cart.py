from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.core import db_session
from src.validators import get_current_active_user
# from src.schemas import CartItemAdd, CartItemUpdate, OrderResponse
# from src.services import get_or_create_cart, add_item_to_cart, recalculate_cart_total, checkout_cart

router = APIRouter(prefix="/cart", tags=["Cart"])


# ============================================================
# --> View Current Cart <--
# ============================================================

@router.get("/")
async def get_cart(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: find or create the CREATED order for current_user, return it
    raise HTTPException(status_code=501, detail="Not implemented yet")


# ============================================================
# --> Add / Update / Remove Items <--
# ============================================================

@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_item(
    # payload: CartItemAdd,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: get_or_create_cart -> check product exists & is_available ->
    #       increase quantity if item already in cart, else create OrderItem ->
    #       recalculate_cart_total
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.patch("/items/{item_id}")
async def update_item_quantity(
    item_id: int,
    # payload: CartItemUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: verify item belongs to current_user's CREATED order ->
    #       update quantity -> recalculate_cart_total
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: verify item belongs to current_user's CREATED order ->
    #       delete OrderItem -> recalculate_cart_total
    raise HTTPException(status_code=501, detail="Not implemented yet")


# ============================================================
# --> Checkout <--
# ============================================================

@router.post("/checkout")
async def checkout(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    # TODO: checkout_cart -> lock in price_at_order for every item ->
    #       recalculate total_price -> set status = PAID
    raise HTTPException(status_code=501, detail="Not implemented yet")