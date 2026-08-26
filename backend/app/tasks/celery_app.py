"""Celery application configuration with scheduled beat schedule."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "sih26006_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ais_tasks",
        "app.tasks.weather_tasks",
        "app.tasks.forecast_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
)

# Scheduled cron beat configuration
celery_app.conf.beat_schedule = {
    "sync-ais-positions-every-5-mins": {
        "task": "app.tasks.ais_tasks.sync_ais_positions_task",
        "schedule": 300.0,  # every 5 minutes
    },
    "sync-weather-conditions-hourly": {
        "task": "app.tasks.weather_tasks.sync_weather_data_task",
        "schedule": 3600.0,  # hourly
    },
    "update-daily-freight-forecasts": {
        "task": "app.tasks.forecast_tasks.run_scheduled_forecasts_task",
        "schedule": crontab(hour=1, minute=0),  # daily at 01:00 UTC
    },
}
