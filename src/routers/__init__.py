from src.routers.admin import router as admin_router
from src.routers.cart import router as cart_router
from src.routers.category import router as category_router
from src.routers.guest_cart import router as guest_cart_router
from src.routers.order import router as order_router
from src.routers.product import router as product_router
from src.routers.review import router as review_router
from src.routers.tag import router as tag_router
from src.routers.user import router as user_router

__all__ = (
    "admin_router",
    "cart_router",
    "category_router",
    "guest_cart_router",
    "order_router",
    "product_router",
    "review_router",
    "tag_router",
    "user_router",
)
