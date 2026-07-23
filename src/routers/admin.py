from fastapi import APIRouter, Depends

from src.models import User
from src.validators import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================
# --> Admin Dashboard — placeholder for future admin-only features
#     (user management, product/category management, analytics, etc.) <--
# ============================================================


@router.get("/dashboard")
async def admin_dashboard(current_admin: User = Depends(require_admin)):
    return {
        "message": f"Welcome, {current_admin.name}. This is the admin dashboard.",
    }
