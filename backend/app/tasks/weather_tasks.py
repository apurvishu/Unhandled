"""Background tasks for weather data synchronization."""

import asyncio
from datetime import datetime, timezone
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_engine
from app.models.port import Port
from app.models.weather_data import WeatherData
from app.tasks.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("weather_tasks")


async def _async_sync_weather():
    logger.info("Executing async weather sync task...")
    async with AsyncSession(async_engine) as db:
        ports_res = await db.execute(select(Port).limit(15))
        ports = ports_res.scalars().all()

        for port in ports:
            # Simulate or fetch maritime weather observation
            wind = round(random.uniform(5.0, 35.0), 1)
            wave = round(random.uniform(0.5, 4.5), 1)
            weather = WeatherData(
                location=port.name,
                latitude=port.latitude,
                longitude=port.longitude,
                timestamp=datetime.now(timezone.utc),
                wind_speed=wind,
                wave_height=wave,
                precipitation=round(random.uniform(0.0, 10.0), 1),
                visibility=round(random.uniform(5.0, 20.0), 1),
                weather_condition="Moderate Breeze" if wind < 20 else "Near Gale",
                source="OPEN_METEO_SIMULATED",
                created_at=datetime.now(timezone.utc),
            )
            db.add(weather)
        await db.commit()
        logger.info(f"Weather conditions recorded for {len(ports)} ports.")


@celery_app.task(name="app.tasks.weather_tasks.sync_weather_data_task")
def sync_weather_data_task():
    """Celery task entrypoint for weather sync."""
    asyncio.run(_async_sync_weather())
    return {"status": "success", "task": "sync_weather_data_task"}
