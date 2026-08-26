"""Freight market API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.vessel import VesselType
from app.schemas.common import StandardResponse
from app.schemas.freight import FreightRateCreate, FreightRateResponse
from app.services.freight_service import FreightService

router = APIRouter(prefix="/freight")


@router.get("", response_model=StandardResponse[list[FreightRateResponse]])
async def get_freight_rates(
    origin: str | None = None,
    destination: str | None = None,
    vessel_type: VesselType | None = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve historical market freight rates."""
    rates = await FreightService.get_historical_rates(
        db, origin=origin, destination=destination, vessel_type=vessel_type, limit=limit
    )
    return StandardResponse(data=rates)


@router.post("", response_model=StandardResponse[FreightRateResponse], status_code=status.HTTP_201_CREATED)
async def record_freight_rate(
    rate_in: FreightRateCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Record a new freight market rate observation (Admin)."""
    rate = await FreightService.record_freight_rate(db, rate_in)
    return StandardResponse(data=rate, message="Freight rate recorded successfully.")


@router.get("/fuel-price", response_model=StandardResponse[dict])
async def get_fuel_price(
    fuel_type: str = "VLSFO",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get latest recorded bunker fuel price."""
    price = await FreightService.get_latest_fuel_price(db, fuel_type=fuel_type) or 620.0
    return StandardResponse(
        data={"fuel_type": fuel_type, "price_per_mt": price, "currency": "USD"}
    )
