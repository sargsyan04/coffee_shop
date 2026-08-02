"""
TODO — Admin user management.

Not registered in src/main.py on purpose — wire it up yourself once the
logic below is implemented, same as the rest of the backend.

Context: frontend/pages/admin.html has a "Пользователи" section that's
currently just a note explaining these endpoints don't exist yet. Once
they do, wire that section up to call them (list + role change + password
reset are the three actions the panel wants to offer).

Suggested endpoints, gated with `Depends(require_admin)` from
src/validators/auth.py:

    GET  /admin/users
        -> list[UserResponse] (or a paginated wrapper), probably with
           search/role filters given how the customer table will grow.

    PATCH /admin/users/{user_id}/role
        body: {"role": "customer" | "barista" | "admin"}
        -> promote/demote an account. Guard against an admin demoting
           themselves into a lockout.

    POST /admin/users/{user_id}/reset-password
        -> generate a temporary password, set must_change_password=True
           (same flag already used for the seeded admin — see
           User.must_change_password in src/models/user.py), and return/
           email it. Reuses the existing force-password-change flow on
           the frontend (frontend/pages/force_password_change.html) with
           no extra frontend work needed.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/admin/users", tags=["Admin — Users"])


@router.get("/")
async def list_users():
    # TODO: implement — see module docstring for the contract the
    # admin panel expects.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin user listing is not implemented yet",
    )


@router.patch("/{user_id}/role")
async def update_user_role(user_id: int):
    # TODO: implement
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin role management is not implemented yet",
    )


@router.post("/{user_id}/reset-password")
async def reset_user_password(user_id: int):
    # TODO: implement
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin password reset is not implemented yet",
    )
