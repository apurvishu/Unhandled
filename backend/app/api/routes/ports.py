"""Port API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.berth import BerthResponse
from app.schemas.common import StandardResponse
from app.schemas.congestion import CongestionDataResponse
from app.schemas.port import PortCreate, PortResponse, PortUpdate
from app.services.port_service import PortService

router = APIRouter(prefix="/ports")


@router.get("", response_model=StandardResponse[list[PortResponse]])
async def list_ports(
    country: str | None = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all global ports."""
    ports = await PortService.list_ports(db, country=country, skip=skip, limit=limit)
    return StandardResponse(data=ports)


@router.get("/{port_id}", response_model=StandardResponse[PortResponse])
async def get_port(
    port_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single port details."""
    port = await PortService.get_port(db, port_id)
    return StandardResponse(data=port)


@router.post("", response_model=StandardResponse[PortResponse], status_code=status.HTTP_201_CREATED)
async def create_port(
    port_in: PortCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PORT_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new port."""
    port = await PortService.create_port(db, port_in)
    return StandardResponse(data=port, message="Port created successfully.")


@router.put("/{port_id}", response_model=StandardResponse[PortResponse])
async def update_port(
    port_id: int,
    port_update: PortUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PORT_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Update port configuration."""
    port = await PortService.update_port(db, port_id, port_update)
    return StandardResponse(data=port, message="Port updated successfully.")


@router.get("/{port_id}/berths", response_model=StandardResponse[list[BerthResponse]])
async def get_port_berths(
    port_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all berths within a port."""
    berths = await PortService.get_berths_for_port(db, port_id)
    return StandardResponse(data=berths)


@router.get("/{port_id}/congestion", response_model=StandardResponse[CongestionDataResponse | None])
async def get_port_congestion(
    port_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get latest congestion status of a port."""
    data = await PortService.get_latest_congestion(db, port_id)
    return StandardResponse(data=data)


@router.get("/{port_id}/vessels", response_model=StandardResponse[list[dict]])
async def get_port_vessels(
    port_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active vessel calls at this port."""
    vessels = await PortService.get_vessels_at_port(db, port_id)
    return StandardResponse(data=vessels)
