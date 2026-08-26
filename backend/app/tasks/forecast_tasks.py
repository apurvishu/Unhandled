"""Background tasks for scheduled ML forecast runs and congestion calculation."""

import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_engine
from app.models.port import Port
from app.models.vessel import VesselType
from app.schemas.freight import FreightForecastRequest
from app.services.forecast_service import ForecastService
from app.tasks.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("forecast_tasks")


async def _async_run_forecasts():
    logger.info("Executing scheduled batch freight forecasts...")
    routes = [
        ("Tubarao", "Qingdao", VesselType.CAPESIZE),
        ("Richards Bay", "Rotterdam", VesselType.CAPESIZE),
        ("Santos", "Singapore", VesselType.PANAMAX),
        ("Dampier", "Qingdao", VesselType.CAPESIZE),
        ("Vancouver", "Yokohama", VesselType.SUPRAMAX),
    ]

    async with AsyncSession(async_engine) as db:
        for origin, dest, v_type in routes:
            req = FreightForecastRequest(
                origin=origin,
                destination=dest,
                vessel_type=v_type,
                forecast_horizon_days=30,
            )
            await ForecastService.generate_freight_forecast(db, req)
        await db.commit()
    logger.info("Batch freight forecasts generated.")


@celery_app.task(name="app.tasks.forecast_tasks.run_scheduled_forecasts_task")
def run_scheduled_forecasts_task():
    """Celery task entrypoint for scheduled ML forecasts."""
    asyncio.run(_async_run_forecasts())
    return {"status": "success", "task": "run_scheduled_forecasts_task"}
