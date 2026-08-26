"""AI/ML Freight rate forecasting API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.vessel import VesselType
from app.schemas.common import StandardResponse
from app.schemas.freight import FreightForecastRequest, FreightForecastResponse
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecast")


@router.get("/freight", response_model=StandardResponse[FreightForecastResponse])
async def get_freight_forecast_get(
    origin: str = Query(..., description="Origin port or region"),
    destination: str = Query(..., description="Destination port or region"),
    vessel_type: VesselType = Query(VesselType.PANAMAX, description="Vessel class"),
    horizon_days: int = Query(30, ge=1, le=365, description="Forecast horizon in days"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve AI/ML freight rate forecast (GET query)."""
    req = FreightForecastRequest(
        origin=origin,
        destination=destination,
        vessel_type=vessel_type,
        forecast_horizon_days=horizon_days,
    )
    forecast = await ForecastService.generate_freight_forecast(db, req)
    return StandardResponse(data=forecast)


@router.post("/freight", response_model=StandardResponse[FreightForecastResponse])
async def post_freight_forecast(
    req: FreightForecastRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI/ML freight rate forecast with confidence bounds and trend analysis (POST body)."""
    forecast = await ForecastService.generate_freight_forecast(db, req)
    return StandardResponse(data=forecast)
