from fastapi import APIRouter

from src.routers.user.auth import router as auth_router
from src.routers.user.profile import router as profile_router
from src.routers.user.reactivation import router as reactivation_router
from src.routers.user.registration import router as registration_router

router = APIRouter(prefix="/user", tags=["Users"])

router.include_router(registration_router)
router.include_router(auth_router)
router.include_router(reactivation_router)
router.include_router(profile_router)

__all__ = ("router",)
