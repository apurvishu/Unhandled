"""Vessel API routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.ship_owner import ShipOwner
from app.models.user import User, UserRole
from app.models.vessel import VesselStatus, VesselType
from app.schemas.ais import AISPositionResponse
from app.schemas.common import StandardResponse
from app.schemas.vessel import VesselCreate, VesselFilter, VesselResponse, VesselUpdate
from app.services.ais_service import AISService
from app.services.vessel_service import VesselService
from app.utils.errors import ForbiddenException, NotFoundException

router = APIRouter(prefix="/vessels")


async def get_ship_owner_id(current_user: User, db: AsyncSession) -> int:
    """Helper to resolve ship_owner_id for the logged in user."""
    if current_user.role == UserRole.ADMIN:
        # If admin, grab the first ship_owner or create dummy
        owner_res = await db.execute(select(ShipOwner))
        owner = owner_res.scalars().first()
        if owner:
            return owner.id
        new_owner = ShipOwner(user_id=current_user.id, company_name="Admin Maritime Fleet")
        db.add(new_owner)
        await db.flush()
        return new_owner.id

    owner_res = await db.execute(select(ShipOwner).where(ShipOwner.user_id == current_user.id))
    owner = owner_res.scalar_one_or_none()
    if owner is None:
        new_owner = ShipOwner(user_id=current_user.id, company_name=f"{current_user.name} Shipping")
        db.add(new_owner)
        await db.flush()
        return new_owner.id
    return owner.id


@router.get("", response_model=StandardResponse[list[VesselResponse]])
async def list_vessels(
    vessel_type: VesselType | None = None,
    min_dwt: float | None = None,
    max_dwt: float | None = None,
    max_draft: float | None = None,
    vessel_status: VesselStatus | None = None,
    availability_before: date | None = None,
    flag: str | None = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List vessels with optional multi-criteria filtering."""
    filters = VesselFilter(
        vessel_type=vessel_type,
        min_dwt=min_dwt,
        max_dwt=max_dwt,
        max_draft=max_draft,
        status=vessel_status,
        availability_before=availability_before,
        flag=flag,
    )
    vessels = await VesselService.list_vessels(db, filters=filters, skip=skip, limit=limit)
    return StandardResponse(data=vessels)


@router.get("/available", response_model=StandardResponse[list[VesselResponse]])
async def get_available_vessels(
    vessel_type: VesselType | None = None,
    min_dwt: float | None = None,
    max_draft: float | None = None,
    available_before: date | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all available vessels ready for chartering."""
    vessels = await VesselService.get_available_vessels(
        db,
        vessel_type=vessel_type,
        min_dwt=min_dwt,
        max_draft=max_draft,
        available_before=available_before,
    )
    return StandardResponse(data=vessels)


@router.get("/near-port/{port_id}", response_model=StandardResponse[list[dict]])
async def get_vessels_near_port(
    port_id: int,
    radius_nm: float = Query(50.0, ge=1.0, le=500.0, description="Radius in nautical miles"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Spatial query returning vessels within a given radius of a port."""
    vessels = await VesselService.get_vessels_near_port(db, port_id=port_id, radius_nm=radius_nm)
    return StandardResponse(data=vessels)


@router.get("/{vessel_id}", response_model=StandardResponse[VesselResponse])
async def get_vessel(
    vessel_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single vessel details."""
    vessel = await VesselService.get_vessel(db, vessel_id)
    return StandardResponse(data=vessel)


@router.get("/{vessel_id}/position", response_model=StandardResponse[AISPositionResponse])
async def get_vessel_position(
    vessel_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get latest AIS geographic coordinates for a vessel."""
    pos = await AISService.get_latest_position(db, vessel_id)
    if pos is None:
        raise NotFoundException("Position for vessel", vessel_id)
    return StandardResponse(data=pos)


@router.post("", response_model=StandardResponse[VesselResponse], status_code=status.HTTP_201_CREATED)
async def create_vessel(
    vessel_in: VesselCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SHIP_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Register a new vessel into the fleet (Ship Owner or Admin)."""
    ship_owner_id = await get_ship_owner_id(current_user, db)
    vessel = await VesselService.create_vessel(db, ship_owner_id=ship_owner_id, vessel_in=vessel_in)
    return StandardResponse(data=vessel, message="Vessel registered successfully.")


@router.put("/{vessel_id}", response_model=StandardResponse[VesselResponse])
async def update_vessel(
    vessel_id: int,
    vessel_update: VesselUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SHIP_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Update vessel specifications or current status."""
    is_admin = current_user.role == UserRole.ADMIN
    ship_owner_id = None if is_admin else await get_ship_owner_id(current_user, db)
    vessel = await VesselService.update_vessel(
        db,
        vessel_id=vessel_id,
        vessel_update=vessel_update,
        ship_owner_id=ship_owner_id,
        is_admin=is_admin,
    )
    return StandardResponse(data=vessel, message="Vessel updated successfully.")


@router.delete("/{vessel_id}", response_model=StandardResponse[dict])
async def delete_vessel(
    vessel_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SHIP_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a vessel from fleet."""
    is_admin = current_user.role == UserRole.ADMIN
    ship_owner_id = None if is_admin else await get_ship_owner_id(current_user, db)
    await VesselService.delete_vessel(
        db, vessel_id=vessel_id, ship_owner_id=ship_owner_id, is_admin=is_admin
    )
    return StandardResponse(data={"deleted": True}, message="Vessel removed successfully.")
