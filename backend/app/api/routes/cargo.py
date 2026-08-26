"""Cargo requirements API routes for procurement officers."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.cargo_requirement import CargoStatus
from app.models.user import User, UserRole
from app.schemas.cargo import CargoCreate, CargoResponse, CargoUpdate
from app.schemas.common import StandardResponse
from app.services.charter_service import CharterService

router = APIRouter(prefix="/cargo")


@router.post("", response_model=StandardResponse[CargoResponse], status_code=status.HTTP_201_CREATED)
async def create_cargo(
    cargo_in: CargoCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    """Post a new cargo requirement (Procurement Officer or Admin)."""
    cargo = await CharterService.create_cargo_requirement(
        db, procurement_user_id=current_user.id, cargo_in=cargo_in
    )
    return StandardResponse(data=cargo, message="Cargo requirement posted successfully.")


@router.get("", response_model=StandardResponse[list[CargoResponse]])
async def list_cargo_requirements(
    cargo_status: CargoStatus | None = None,
    my_cargo_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List open cargo requirements with filtering."""
    user_id = current_user.id if my_cargo_only else None
    items = await CharterService.list_cargo_requirements(
        db, user_id=user_id, status=cargo_status, skip=skip, limit=limit
    )
    return StandardResponse(data=items)


@router.get("/{cargo_id}", response_model=StandardResponse[CargoResponse])
async def get_cargo_requirement(
    cargo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single cargo requirement details."""
    cargo = await CharterService.get_cargo_requirement(db, cargo_id)
    return StandardResponse(data=CargoResponse.model_validate(cargo))


@router.put("/{cargo_id}", response_model=StandardResponse[CargoResponse])
async def update_cargo_requirement(
    cargo_id: int,
    cargo_update: CargoUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    """Update a cargo requirement."""
    is_admin = current_user.role == UserRole.ADMIN
    cargo = await CharterService.update_cargo_requirement(
        db,
        cargo_id=cargo_id,
        cargo_update=cargo_update,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return StandardResponse(data=cargo, message="Cargo requirement updated successfully.")


@router.delete("/{cargo_id}", response_model=StandardResponse[dict])
async def delete_cargo_requirement(
    cargo_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a cargo requirement."""
    is_admin = current_user.role == UserRole.ADMIN
    await CharterService.delete_cargo_requirement(
        db, cargo_id=cargo_id, user_id=current_user.id, is_admin=is_admin
    )
    return StandardResponse(data={"deleted": True}, message="Cargo requirement removed.")
