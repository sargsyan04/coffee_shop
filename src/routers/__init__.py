from src.routers.product import router as product_router
from src.routers.category import router as category_router
from src.routers.user import router as user_router
from src.routers.admin import router as admin_router


routers = (
    user_router, category_router, product_router, admin_router
)

__all__ = ('routers',)