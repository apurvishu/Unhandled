"""Port Congestion and prediction API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.congestion_data import CongestionLevel
from app.models.user import User, UserRole
from app.schemas.common import StandardResponse
from app.schemas.congestion import (
    CongestionDataResponse,
    CongestionPredictionRequest,
    CongestionPredictionResponse,
)
from app.services.congestion_service import CongestionService
from app.services.port_service import PortService

router = APIRouter(prefix="/congestion")


@router.get("/{port_id}", response_model=StandardResponse[CongestionDataResponse | None])
async def get_port_congestion(
    port_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the most recent recorded congestion status for a port."""
    data = await PortService.get_latest_congestion(db, port_id)
    return StandardResponse(data=data)


@router.post("/predict", response_model=StandardResponse[CongestionPredictionResponse])
async def predict_port_congestion(
    req: CongestionPredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Run ML inference to forecast port congestion and waiting time."""
    pred = await CongestionService.predict_port_congestion(db, req)
    return StandardResponse(data=pred)
