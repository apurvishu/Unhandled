"""Background tasks for periodic AIS tracking synchronization."""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import async_engine
from app.models.ais_position import AISPosition
from app.models.vessel import Vessel
from app.services.ais_service import AISService
from app.tasks.celery_app import celery_app
from app.utils.logging import get_logger

logger = get_logger("ais_tasks")


async def _async_sync_ais():
    logger.info("Executing async AIS sync task...")
    from sqlalchemy.ext.asyncio import AsyncSession
    async with AsyncSession(async_engine) as db:
        vessels_res = await db.execute(select(Vessel).limit(20))
        vessels = vessels_res.scalars().all()

        provider = AISService.get_provider()
        for v in vessels:
            pos_data = await provider.get_vessel_position(v.imo_number)
            if pos_data:
                geom = f"SRID=4326;POINT({pos_data['longitude']} {pos_data['latitude']})"
                ais_pos = AISPosition(
                    vessel_id=v.id,
                    timestamp=datetime.now(timezone.utc),
                    latitude=pos_data["latitude"],
                    longitude=pos_data["longitude"],
                    speed=pos_data.get("speed"),
                    course=pos_data.get("course"),
                    heading=pos_data.get("heading"),
                    destination=pos_data.get("destination"),
                    position=geom,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(ais_pos)
                v.current_position = geom
        await db.commit()
        logger.info(f"Updated AIS telemetry for {len(vessels)} vessels.")


@celery_app.task(name="app.tasks.ais_tasks.sync_ais_positions_task")
def sync_ais_positions_task():
    """Celery entrypoint for AIS position sync."""
    asyncio.run(_async_sync_ais())
    return {"status": "success", "task": "sync_ais_positions_task"}
