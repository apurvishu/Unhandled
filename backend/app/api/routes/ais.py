"""AIS Ingestion and Query API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.ais import AISPositionResponse, VesselPositionUpdate, VesselTrackResponse
from app.schemas.common import StandardResponse
from app.services.ais_service import AISService
from app.services.port_service import PortService
from app.utils.errors import NotFoundException

router = APIRouter(prefix="/ais")


@router.post("/positions/{vessel_id}", response_model=StandardResponse[AISPositionResponse], status_code=status.HTTP_201_CREATED)
async def ingest_ais_position(
    vessel_id: int,
    pos_in: VesselPositionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Ingest normalized AIS position data point into PostGIS."""
    record = await AISService.record_position(db, vessel_id=vessel_id, pos_in=pos_in)
    return StandardResponse(
        data=AISPositionResponse.model_validate(record),
        message="AIS position recorded successfully.",
    )


@router.get("/vessel/{vessel_id}/position", response_model=StandardResponse[AISPositionResponse])
async def get_vessel_current_position(
    vessel_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch current live or simulated position for a vessel."""
    pos = await AISService.get_latest_position(db, vessel_id)
    if pos is None:
        raise NotFoundException("Position for vessel", vessel_id)
    return StandardResponse(data=pos)


@router.get("/vessel/{vessel_id}/track", response_model=StandardResponse[VesselTrackResponse])
async def get_vessel_track(
    vessel_id: int,
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch historical AIS track coordinates for voyage path visualization."""
    track = await AISService.get_vessel_track(db, vessel_id, limit=limit)
    return StandardResponse(data=track)


@router.get("/near-port/{port_id}", response_model=StandardResponse[list[dict]])
async def get_ais_vessels_near_port(
    port_id: int,
    radius_nm: float = Query(50.0, ge=1.0, le=200.0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Query AIS provider for nearby live vessels around a port."""
    port = await PortService.get_port_by_id(db, port_id)
    provider = AISService.get_provider()
    vessels = await provider.get_vessels_near_port(
        latitude=port.latitude,
        longitude=port.longitude,
        radius_nm=radius_nm,
    )
    return StandardResponse(data=vessels)
