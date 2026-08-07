""" 
TODO — Guest (unauthenticated) checkout.

Not registered in src/main.py on purpose — wire it up yourself once the
logic below is implemented, same as the rest of the backend.

Context: the frontend now lets a visitor build a cart entirely client-side
(localStorage, see frontend/js/cart-store.js) before creating an account —
add/update/remove all work with zero backend calls. The only step that
still needs a real endpoint is finishing the order, because today every
route in src/routers/cart.py and src/routers/order.py requires
get_current_active_user.

frontend/js/cart.js already calls the endpoint below and handles a 501
gracefully (it tells the guest to log in / register instead), so nothing
on the frontend needs to change once this is implemented.

Expected request, sent by frontend/js/cart.js on guest checkout:

    POST /cart/guest/checkout
    {
      "items": [{"product_id": 1, "quantity": 2}, ...],
      "contact": {"name": "...", "phone": "...", "email": "..." | null}
    }

Things you'll need to decide before implementing:
  - Does a guest order need a User row at all (e.g. a lightweight
    "guest" user created on the fly, matched by phone/email on repeat
    visits), or should Order.user_id become nullable?
  - Re-validate prices/stock server-side from `items` — never trust the
    client-supplied price, only product_id + quantity.
  - What status should the created order start in (CREATED vs PAID) —
    depends on how payment actually happens in this project.
  - Response shape should match schemas.order.OrderResponse so it can
    reuse the same rendering path as the logged-in checkout flow.
"""

from fastapi import APIRouter, HTTPException, status, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.session import get_or_create_guest_session_id
from src.core import db_session
from src.validators.auth import get_optional_current_user
from src.models import User
from src.schemas import GuestCheckoutRequest, OrderResponse
from src.services import guest_checkout_service


router = APIRouter(prefix="/cart/guest", tags=["Guest Cart"])


@router.post("/checkout", response_model=OrderResponse)
async def guest_checkout(
    payload: GuestCheckoutRequest,
    request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    session: AsyncSession = Depends(db_session),
):
    if current_user:
     raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This endpoint is only for guests.",
    )

    guest_session_id = get_or_create_guest_session_id(request)

    return await guest_checkout_service(
        session=session,
        payload=payload,
        guest_session_id=guest_session_id,
        # TODO: Use guest_session_id to reconnect guest carts
        # during the same browser session.
) 