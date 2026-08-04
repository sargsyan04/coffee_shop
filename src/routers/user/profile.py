from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import db_session, delete_image, save_image
from src.models import RefreshToken, User
from src.schemas import (
    ChangePasswordRequest,
    MessageResponse,
    UserResponse,
    UserSettingsUpdate,
    UserStatusResponse,
)
from src.services import hash_password
from src.validators import get_current_active_user, get_current_user, validate_password

router = APIRouter()


@router.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Return the profile of the currently authenticated, active user."""
    return current_user


@router.get("/status", response_model=UserStatusResponse, status_code=status.HTTP_200_OK)
async def get_user_status(current_user: User = Depends(get_current_user)):
    """Return account status flags, reachable even for accounts that must change their password."""
    return current_user


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    """Deactivate the account instead of deleting it, keeping order/review history intact."""
    # Soft delete: deactivate instead of physically removing the row.
    # Orders and reviews stay untouched, so history is preserved for analytics.
    current_user.is_active = False
    current_user.deactivated_at = datetime.now(UTC)

    # Revoke all refresh tokens so a lingering token can't be used
    # to obtain a new access token after deactivation
    await session.execute(update(RefreshToken).where(RefreshToken.user_id == current_user.id).values(is_revoked=True))

    await session.commit()


@router.patch("/change-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_session),
):
    """Change the password, reachable even when must_change_password forces the flow."""
    if not current_user.must_change_password:
        # Regular password change: current_password is mandatory here
        if not payload.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required.",
            )

        is_valid = validate_password(payload.current_password, current_user.hashed_password.encode("utf-8"))
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

    hashed_bytes = hash_password(payload.new_password)
    current_user.hashed_password = hashed_bytes.decode("utf-8")
    current_user.must_change_password = False

    await session.commit()

    return {"detail": "Password changed successfully."}


@router.post("/image", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def upload_user_image(
    current_user: User = Depends(get_current_active_user),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(db_session),
):
    """Replace the user's avatar, discarding the previous file if one exists."""
    delete_image(current_user.image_url)
    current_user.image_url = save_image(file, filename_prefix="User", entity_id=current_user.id, folder="users")

    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.patch("/update", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def user_settings(
    update_user: UserSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db_session),
):
    """Apply a partial update to the user's own settings."""
    change_data = update_user.model_dump(exclude_unset=True)
    for field, value in change_data.items():
        setattr(current_user, field, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return {"detail": "Changes saved successfully."}
