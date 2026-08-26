"""User management routes with role-based authorization."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.common import StandardResponse
from app.schemas.user import UserResponse, UserUpdate
from app.utils.errors import ForbiddenException, NotFoundException

router = APIRouter(prefix="/users")


@router.get("", response_model=StandardResponse[list[UserResponse]])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all users (Admin only)."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return StandardResponse(data=[UserResponse.model_validate(u) for u in users])


@router.get("/{user_id}", response_model=StandardResponse[UserResponse])
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a user by ID (Self or Admin)."""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise ForbiddenException("You can only view your own user profile.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundException("User", user_id)

    return StandardResponse(data=UserResponse.model_validate(user))


@router.put("/{user_id}", response_model=StandardResponse[UserResponse])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a user (Self or Admin)."""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise ForbiddenException("You can only edit your own user profile.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundException("User", user_id)

    update_data = user_update.model_dump(exclude_unset=True)

    # Only admins can change roles or active status
    if current_user.role != UserRole.ADMIN:
        update_data.pop("role", None)
        update_data.pop("is_active", None)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return StandardResponse(data=UserResponse.model_validate(user))


@router.delete("/{user_id}", response_model=StandardResponse[dict])
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate/delete user account (Admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundException("User", user_id)

    await db.delete(user)
    await db.flush()
    return StandardResponse(data={"deleted": True}, message="User deleted successfully.")
