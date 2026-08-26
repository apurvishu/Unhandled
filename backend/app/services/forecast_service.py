"""Forecast service interfacing with ML freight forecasting engine."""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.forecasting import FreightForecaster
from app.models.forecast_result import ForecastResult
from app.models.freight_rate import FreightRate
from app.models.fuel_price import FuelPrice
from app.models.vessel import VesselType
from app.schemas.freight import FreightForecastRequest, FreightForecastResponse


class ForecastService:
    @classmethod
    async def generate_freight_forecast(
        cls, db: AsyncSession, req: FreightForecastRequest
    ) -> FreightForecastResponse:
        # Retrieve recent historical rates for context
        hist_query = (
            select(FreightRate.rate)
            .where(
                FreightRate.origin.ilike(f"%{req.origin}%"),
                FreightRate.destination.ilike(f"%{req.destination}%"),
                FreightRate.vessel_type == req.vessel_type,
            )
            .order_by(FreightRate.rate_date.desc())
            .limit(10)
        )
        hist_res = await db.execute(hist_query)
        recent_rates = list(hist_res.scalars().all())

        # Retrieve recent fuel price
        fuel_res = await db.execute(
            select(FuelPrice.price).order_by(FuelPrice.price_date.desc()).limit(1)
        )
        fuel_price = fuel_res.scalar_one_or_none()

        # Run inference
        forecast = FreightForecaster.predict_freight_rate(
            origin=req.origin,
            destination=req.destination,
            vessel_type=req.vessel_type,
            horizon_days=req.forecast_horizon_days,
            recent_historical_rates=recent_rates,
            recent_fuel_price=fuel_price,
        )

        # Store forecast result in database
        result_record = ForecastResult(
            route=f"{req.origin}->{req.destination}",
            vessel_type=req.vessel_type.value,
            forecast_date=forecast.forecast_date,
            predicted_rate=forecast.predicted_rate,
            lower_bound=forecast.lower_bound,
            upper_bound=forecast.upper_bound,
            confidence=forecast.confidence,
            model_version=forecast.model_version,
            created_at=datetime.now(timezone.utc),
        )
        db.add(result_record)
        await db.flush()

        return forecast
