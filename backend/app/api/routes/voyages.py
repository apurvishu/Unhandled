"""Voyage and Port Call tracking routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.port_call import PortCall, PortCallStatus
from app.models.user import User, UserRole
from app.models.voyage import Voyage, VoyageStatus
from app.schemas.common import StandardResponse
from app.schemas.voyage import (
    PortCallCreate,
    PortCallResponse,
    PortCallUpdate,
    VoyageCreate,
    VoyageResponse,
    VoyageUpdate,
)
from app.utils.errors import NotFoundException

router = APIRouter(prefix="/voyages")


@router.post("", response_model=StandardResponse[VoyageResponse], status_code=status.HTTP_201_CREATED)
async def create_voyage(
    voyage_in: VoyageCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SHIP_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a new voyage track."""
    voyage = Voyage(
        vessel_id=voyage_in.vessel_id,
        cargo_requirement_id=voyage_in.cargo_requirement_id,
        origin_port_id=voyage_in.origin_port_id,
        destination_port_id=voyage_in.destination_port_id,
        departure_time=voyage_in.departure_time,
        estimated_arrival=voyage_in.estimated_arrival,
        status=VoyageStatus.PLANNED,
        estimated_cost=voyage_in.estimated_cost,
        created_at=datetime.now(timezone.utc),
    )
    db.add(voyage)
    await db.flush()
    await db.refresh(voyage)
    return StandardResponse(data=VoyageResponse.model_validate(voyage), message="Voyage created successfully.")


@router.get("", response_model=StandardResponse[list[VoyageResponse]])
async def list_voyages(
    vessel_id: int | None = None,
    voyage_status: VoyageStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List voyages with optional filtering."""
    query = select(Voyage)
    if vessel_id:
        query = query.where(Voyage.vessel_id == vessel_id)
    if voyage_status:
        query = query.where(Voyage.status == voyage_status)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    voyages = result.scalars().all()
    return StandardResponse(data=[VoyageResponse.model_validate(v) for v in voyages])


@router.get("/{voyage_id}", response_model=StandardResponse[VoyageResponse])
async def get_voyage(
    voyage_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single voyage details."""
    result = await db.execute(select(Voyage).where(Voyage.id == voyage_id))
    voyage = result.scalar_one_or_none()
    if voyage is None:
        raise NotFoundException("Voyage", voyage_id)
    return StandardResponse(data=VoyageResponse.model_validate(voyage))


@router.put("/{voyage_id}", response_model=StandardResponse[VoyageResponse])
async def update_voyage(
    voyage_id: int,
    voyage_update: VoyageUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SHIP_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Update voyage progress and actuals."""
    result = await db.execute(select(Voyage).where(Voyage.id == voyage_id))
    voyage = result.scalar_one_or_none()
    if voyage is None:
        raise NotFoundException("Voyage", voyage_id)

    update_data = voyage_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(voyage, field, value)

    await db.flush()
    await db.refresh(voyage)
    return StandardResponse(data=VoyageResponse.model_validate(voyage), message="Voyage updated.")


@router.post("/{voyage_id}/port-calls", response_model=StandardResponse[PortCallResponse], status_code=status.HTTP_201_CREATED)
async def create_port_call(
    voyage_id: int,
    port_call_in: PortCallCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Schedule a port call for a voyage."""
    port_call = PortCall(
        voyage_id=voyage_id,
        port_id=port_call_in.port_id,
        berth_id=port_call_in.berth_id,
        eta=port_call_in.eta,
        etd=port_call_in.etd,
        status=PortCallStatus.SCHEDULED,
        created_at=datetime.now(timezone.utc),
    )
    db.add(port_call)
    await db.flush()
    await db.refresh(port_call)
    return StandardResponse(data=PortCallResponse.model_validate(port_call))
