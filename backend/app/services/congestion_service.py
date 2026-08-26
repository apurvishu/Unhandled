"""Congestion service linking port data with ML congestion predictor."""

from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.congestion import CongestionPredictor
from app.models.berth import Berth
from app.models.congestion_data import CongestionData, CongestionLevel
from app.models.port import Port
from app.schemas.congestion import (
    CongestionDataResponse,
    CongestionPredictionRequest,
    CongestionPredictionResponse,
)
from app.utils.errors import NotFoundException


class CongestionService:
    @classmethod
    async def record_congestion(
        cls,
        db: AsyncSession,
        port_id: int,
        vessels_waiting: int,
        vessels_at_berth: int,
        avg_waiting_time: float,
        berth_utilization: float,
        level: CongestionLevel,
        predicted_waiting: float | None = None,
    ) -> CongestionData:
        data = CongestionData(
            port_id=port_id,
            timestamp=datetime.now(timezone.utc),
            vessels_waiting=vessels_waiting,
            vessels_at_berth=vessels_at_berth,
            average_waiting_time=avg_waiting_time,
            berth_utilization=berth_utilization,
            congestion_level=level,
            predicted_waiting_time=predicted_waiting,
            created_at=datetime.now(timezone.utc),
        )
        db.add(data)
        await db.flush()
        await db.refresh(data)
        return data

    @classmethod
    async def predict_port_congestion(
        cls, db: AsyncSession, req: CongestionPredictionRequest
    ) -> CongestionPredictionResponse:
        # Check port exists
        port_res = await db.execute(select(Port).where(Port.id == req.port_id))
        port = port_res.scalar_one_or_none()
        if port is None:
            raise NotFoundException("Port", req.port_id)

        # Count total berths
        berths_res = await db.execute(
            select(func.count(Berth.id)).where(Berth.port_id == req.port_id)
        )
        berth_count = berths_res.scalar() or 8

        # Get latest congestion data if available
        cong_res = await db.execute(
            select(CongestionData)
            .where(CongestionData.port_id == req.port_id)
            .order_by(CongestionData.timestamp.desc())
            .limit(1)
        )
        latest = cong_res.scalar_one_or_none()

        curr_waiting = latest.vessels_waiting if latest and latest.vessels_waiting is not None else 3
        curr_at_berth = latest.vessels_at_berth if latest and latest.vessels_at_berth is not None else min(5, berth_count)

        return CongestionPredictor.predict_congestion(
            port_id=req.port_id,
            horizon_hours=req.horizon_hours,
            current_waiting=curr_waiting,
            current_at_berth=curr_at_berth,
            berth_capacity=berth_count,
        )
