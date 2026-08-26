"""Port congestion prediction ML module."""

from datetime import datetime, timezone
import numpy as np

from app.core.config import settings
from app.ml.model_loader import ModelLoader
from app.models.congestion_data import CongestionLevel
from app.schemas.congestion import CongestionPredictionResponse
from app.utils.logging import get_logger

logger = get_logger("ml_congestion")


class CongestionPredictor:
    @classmethod
    def predict_congestion(
        cls,
        port_id: int,
        horizon_hours: int = 24,
        current_waiting: int = 4,
        current_at_berth: int = 8,
        berth_capacity: int = 10,
    ) -> CongestionPredictionResponse:
        model = ModelLoader.load_model("congestion", settings.CONGESTION_MODEL_VERSION)

        base_utilization = min(100.0, (current_at_berth / max(1, berth_capacity)) * 100.0)

        if model is not None:
            try:
                features = np.array([[current_waiting, current_at_berth, berth_capacity, horizon_hours]])
                pred = model.predict(features)[0]
                waiting_time = float(pred[0])
                berth_util = float(pred[1])
            except Exception as e:
                logger.warning(f"Congestion ML inference fallback: {e}")
                waiting_time = (current_waiting * 3.5) + (horizon_hours * 0.2)
                berth_util = min(98.0, base_utilization + (horizon_hours * 0.15))
        else:
            # Deterministic queue simulation
            waiting_time = (current_waiting * 3.2) + (horizon_hours * 0.15)
            berth_util = min(98.0, base_utilization + (horizon_hours * 0.1))

        waiting_time = round(max(1.0, waiting_time), 1)
        berth_util = round(min(100.0, max(10.0, berth_util)), 1)
        vessels_expected = int(current_waiting + round(horizon_hours / 12.0))

        # Classify congestion level
        if waiting_time > 48 or berth_util > 90:
            level = CongestionLevel.CRITICAL
        elif waiting_time > 24 or berth_util > 75:
            level = CongestionLevel.HIGH
        elif waiting_time > 10 or berth_util > 50:
            level = CongestionLevel.MEDIUM
        else:
            level = CongestionLevel.LOW

        confidence = round(max(0.70, 0.95 - (horizon_hours * 0.002)), 2)

        return CongestionPredictionResponse(
            port_id=port_id,
            congestion_level=level,
            predicted_waiting_time=waiting_time,
            berth_utilization=berth_util,
            vessels_expected=vessels_expected,
            confidence=confidence,
            prediction_horizon_hours=horizon_hours,
        )
