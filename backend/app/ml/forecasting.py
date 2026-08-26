"""Freight rate forecasting ML module."""

from datetime import date, datetime, timedelta, timezone
import math
import numpy as np

from app.core.config import settings
from app.ml.model_loader import ModelLoader
from app.models.vessel import VesselType
from app.schemas.freight import FreightForecastResponse
from app.utils.logging import get_logger

logger = get_logger("ml_forecasting")


class FreightForecaster:
    @staticmethod
    def _base_rate_for_vessel(vessel_type: VesselType) -> float:
        base_rates = {
            VesselType.CAPESIZE: 18.5,
            VesselType.PANAMAX: 24.2,
            VesselType.SUPRAMAX: 28.0,
            VesselType.OTHER: 22.0,
        }
        return base_rates.get(vessel_type, 22.0)

    @classmethod
    def predict_freight_rate(
        cls,
        origin: str,
        destination: str,
        vessel_type: VesselType,
        horizon_days: int = 30,
        recent_historical_rates: list[float] | None = None,
        recent_fuel_price: float | None = None,
    ) -> FreightForecastResponse:
        model = ModelLoader.load_model("freight", settings.FREIGHT_MODEL_VERSION)

        base_rate = cls._base_rate_for_vessel(vessel_type)

        # Route factor based on origin & destination hash
        route_factor = 1.0 + (abs(hash(f"{origin}->{destination}")) % 30) / 100.0

        if recent_historical_rates and len(recent_historical_rates) > 0:
            avg_hist = sum(recent_historical_rates) / len(recent_historical_rates)
            current_rate = avg_hist
        else:
            current_rate = base_rate * route_factor

        # Fuel factor adjustment
        fuel_factor = (recent_fuel_price / 600.0) if recent_fuel_price else 1.05

        if model is not None:
            try:
                # Features: [base_rate, current_rate, horizon_days, fuel_factor]
                features = np.array([[base_rate, current_rate, horizon_days, fuel_factor]])
                predicted_rate = float(model.predict(features)[0])
            except Exception as e:
                logger.warning(f"ML model inference failed, falling back to statistical method: {e}")
                predicted_rate = current_rate * (1.0 + math.sin(horizon_days / 15.0) * 0.08)
        else:
            # Statistical forecast simulation
            seasonal_drift = math.sin(horizon_days / 12.0) * 0.06
            predicted_rate = current_rate * fuel_factor * (1.0 + seasonal_drift)

        predicted_rate = round(max(5.0, predicted_rate), 2)
        uncertainty = round(0.05 + (horizon_days / 365.0) * 0.15, 3)
        lower_bound = round(predicted_rate * (1.0 - uncertainty), 2)
        upper_bound = round(predicted_rate * (1.0 + uncertainty), 2)
        confidence = round(max(0.65, 0.95 - (horizon_days * 0.001)), 2)

        # Determine trend
        rate_diff = predicted_rate - current_rate
        if rate_diff > 0.5:
            trend = "INCREASING"
            recommendation = "BOOK_NOW"
        elif rate_diff < -0.5:
            trend = "DECREASING"
            recommendation = "WAIT"
        else:
            trend = "STABLE"
            recommendation = "NEUTRAL"

        return FreightForecastResponse(
            predicted_rate=predicted_rate,
            currency="USD",
            unit="MT",
            confidence=confidence,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            trend=trend,
            recommendation=recommendation,
            model_version=settings.FREIGHT_MODEL_VERSION,
            forecast_date=date.today() + timedelta(days=horizon_days),
        )
