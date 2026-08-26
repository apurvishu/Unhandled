"""Berth API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.berth import BerthCreate, BerthResponse, BerthUpdate
from app.schemas.common import StandardResponse
from app.services.port_service import PortService

router = APIRouter(prefix="/berths")


@router.post("/port/{port_id}", response_model=StandardResponse[BerthResponse], status_code=status.HTTP_201_CREATED)
async def create_berth(
    port_id: int,
    berth_in: BerthCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PORT_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new berth at a specific port."""
    berth = await PortService.create_berth(db, port_id=port_id, berth_in=berth_in)
    return StandardResponse(data=berth, message="Berth created successfully.")


@router.put("/{berth_id}", response_model=StandardResponse[BerthResponse])
async def update_berth(
    berth_id: int,
    berth_update: BerthUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PORT_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Update berth status or specifications."""
    berth = await PortService.update_berth(db, berth_id=berth_id, berth_update=berth_update)
    return StandardResponse(data=berth, message="Berth updated successfully.")
