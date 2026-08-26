"""Freight service for rates and market indicators."""

from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.freight_rate import FreightRate
from app.models.fuel_price import FuelPrice
from app.models.commodity_price import CommodityPrice
from app.models.vessel import VesselType
from app.schemas.freight import FreightRateCreate, FreightRateResponse
from app.utils.errors import NotFoundException


class FreightService:
    @classmethod
    async def record_freight_rate(
        cls, db: AsyncSession, rate_in: FreightRateCreate
    ) -> FreightRateResponse:
        rate = FreightRate(
            origin=rate_in.origin,
            destination=rate_in.destination,
            vessel_type=rate_in.vessel_type,
            rate=rate_in.rate,
            currency=rate_in.currency,
            rate_date=rate_in.rate_date,
            source=rate_in.source,
            created_at=datetime.now(timezone.utc),
        )
        db.add(rate)
        await db.flush()
        await db.refresh(rate)
        return FreightRateResponse.model_validate(rate)

    @classmethod
    async def get_historical_rates(
        cls,
        db: AsyncSession,
        origin: str | None = None,
        destination: str | None = None,
        vessel_type: VesselType | None = None,
        limit: int = 50,
    ) -> list[FreightRateResponse]:
        query = select(FreightRate).order_by(FreightRate.rate_date.desc())
        if origin:
            query = query.where(FreightRate.origin.ilike(f"%{origin}%"))
        if destination:
            query = query.where(FreightRate.destination.ilike(f"%{destination}%"))
        if vessel_type:
            query = query.where(FreightRate.vessel_type == vessel_type)
        query = query.limit(limit)

        result = await db.execute(query)
        rates = result.scalars().all()
        return [FreightRateResponse.model_validate(r) for r in rates]

    @classmethod
    async def get_latest_fuel_price(
        cls, db: AsyncSession, fuel_type: str = "VLSFO"
    ) -> float | None:
        result = await db.execute(
            select(FuelPrice)
            .where(FuelPrice.fuel_type.ilike(f"%{fuel_type}%"))
            .order_by(FuelPrice.price_date.desc())
            .limit(1)
        )
        fuel = result.scalar_one_or_none()
        return fuel.price if fuel else None
