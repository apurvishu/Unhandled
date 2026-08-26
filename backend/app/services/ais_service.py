"""AIS Service layer with pluggable AIS Provider architecture and mock/live separation."""

import abc
from datetime import datetime, timezone
import math
from typing import Any, Protocol

from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeomFromText
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ais_position import AISPosition
from app.models.port import Port
from app.models.vessel import Vessel
from app.schemas.ais import AISPositionResponse, VesselPositionUpdate, VesselTrackResponse
from app.utils.errors import NotFoundException
from app.utils.logging import get_logger

logger = get_logger("ais_service")


class AISProvider(abc.ABC):
    """Abstract interface for pluggable AIS data providers."""

    @abc.abstractmethod
    async def get_vessel_position(self, imo_number: str) -> dict[str, Any] | None:
        """Fetch current position for a vessel by IMO number."""
        pass

    @abc.abstractmethod
    async def get_vessel_track(
        self, imo_number: str, hours: int = 24
    ) -> list[dict[str, Any]]:
        """Fetch historical track for a vessel."""
        pass

    @abc.abstractmethod
    async def get_vessel_eta(
        self, imo_number: str, destination_port: str
    ) -> dict[str, Any] | None:
        """Calculate or fetch ETA for a vessel to destination."""
        pass

    @abc.abstractmethod
    async def get_vessels_near_port(
        self, latitude: float, longitude: float, radius_nm: float = 50.0
    ) -> list[dict[str, Any]]:
        """Fetch vessels currently within radius of port coordinates."""
        pass


class MockAISProvider(AISProvider):
    """
    Simulated AIS provider for local development, testing, and offline modes.
    Generates realistic maritime trajectories and positions.
    """

    DATA_SOURCE = "SIMULATED_AIS_DATA"

    async def get_vessel_position(self, imo_number: str) -> dict[str, Any] | None:
        # Deterministic simulation based on hash of IMO
        h = hash(imo_number)
        base_lat = 1.290270 + (h % 100) * 0.05  # Singapore region baseline
        base_lon = 103.851959 + ((h >> 4) % 100) * 0.05
        return {
            "imo_number": imo_number,
            "latitude": round(base_lat, 6),
            "longitude": round(base_lon, 6),
            "speed": round(12.5 + (h % 5), 1),
            "course": round((h % 360) * 1.0, 1),
            "heading": round((h % 360) * 1.0, 1),
            "destination": "SG SIN",
            "eta": datetime.now(timezone.utc),
            "navigation_status": "Underway using engine",
            "source": self.DATA_SOURCE,
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_vessel_track(
        self, imo_number: str, hours: int = 24
    ) -> list[dict[str, Any]]:
        pos = await self.get_vessel_position(imo_number)
        if not pos:
            return []
        track = []
        for i in range(min(hours, 24)):
            lat = pos["latitude"] - (i * 0.05)
            lon = pos["longitude"] - (i * 0.05)
            track.append({
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "speed": pos["speed"],
                "course": pos["course"],
                "heading": pos["heading"],
                "timestamp": datetime.now(timezone.utc),
                "source": self.DATA_SOURCE,
            })
        return track

    async def get_vessel_eta(
        self, imo_number: str, destination_port: str
    ) -> dict[str, Any] | None:
        return {
            "imo_number": imo_number,
            "destination_port": destination_port,
            "estimated_eta": datetime.now(timezone.utc),
            "estimated_distance_nm": 180.5,
            "average_speed_knots": 13.2,
            "source": self.DATA_SOURCE,
        }

    async def get_vessels_near_port(
        self, latitude: float, longitude: float, radius_nm: float = 50.0
    ) -> list[dict[str, Any]]:
        return [
            {
                "imo_number": f"IMO9{i}34567",
                "vessel_name": f"Simulated Vessel {i}",
                "latitude": latitude + (i * 0.02),
                "longitude": longitude + (i * 0.02),
                "speed": 10.0 + i,
                "course": 45.0 * i,
                "source": self.DATA_SOURCE,
            }
            for i in range(1, 4)
        ]


class LiveAISProvider(AISProvider):
    """
    Live commercial AIS provider integration (e.g. Spire, MarineTraffic, AISStream).
    Activated when AIS_API_KEY is configured in environment.
    """

    DATA_SOURCE = "LIVE_AIS_DATA"

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    async def get_vessel_position(self, imo_number: str) -> dict[str, Any] | None:
        # Plug external HTTP client call here
        logger.info(f"Fetching live AIS position for IMO: {imo_number}")
        # In case live connection is configured
        return None

    async def get_vessel_track(
        self, imo_number: str, hours: int = 24
    ) -> list[dict[str, Any]]:
        return []

    async def get_vessel_eta(
        self, imo_number: str, destination_port: str
    ) -> dict[str, Any] | None:
        return None

    async def get_vessels_near_port(
        self, latitude: float, longitude: float, radius_nm: float = 50.0
    ) -> list[dict[str, Any]]:
        return []


class AISService:
    """Service to orchestrate AIS data, record positions in PostGIS, and serve queries."""

    _provider: AISProvider | None = None

    @classmethod
    def get_provider(cls) -> AISProvider:
        if cls._provider is None:
            if settings.AIS_API_KEY and settings.AIS_API_URL:
                logger.info("Initializing LiveAISProvider")
                cls._provider = LiveAISProvider(settings.AIS_API_KEY, settings.AIS_API_URL)
            else:
                logger.info("Initializing MockAISProvider (Simulated)")
                cls._provider = MockAISProvider()
        return cls._provider

    @classmethod
    async def record_position(
        cls, db: AsyncSession, vessel_id: int, pos_in: VesselPositionUpdate
    ) -> AISPosition:
        """Store normalized position into ais_positions and update Vessel.current_position."""
        vessel_res = await db.execute(select(Vessel).where(Vessel.id == vessel_id))
        vessel = vessel_res.scalar_one_or_none()
        if vessel is None:
            raise NotFoundException("Vessel", vessel_id)

        geom = WKTElement(f"POINT({pos_in.longitude} {pos_in.latitude})", srid=4326)

        ais_record = AISPosition(
            vessel_id=vessel_id,
            timestamp=datetime.now(timezone.utc),
            latitude=pos_in.latitude,
            longitude=pos_in.longitude,
            speed=pos_in.speed,
            course=pos_in.course,
            heading=pos_in.heading,
            destination=pos_in.destination,
            eta=pos_in.eta,
            navigation_status=pos_in.navigation_status,
            position=geom,
            created_at=datetime.now(timezone.utc),
        )
        db.add(ais_record)

        # Update current vessel position
        vessel.current_position = geom
        await db.flush()
        await db.refresh(ais_record)
        return ais_record

    @classmethod
    async def get_latest_position(
        cls, db: AsyncSession, vessel_id: int
    ) -> AISPositionResponse | None:
        result = await db.execute(
            select(AISPosition)
            .where(AISPosition.vessel_id == vessel_id)
            .order_by(AISPosition.timestamp.desc())
            .limit(1)
        )
        pos = result.scalar_one_or_none()
        if pos is None:
            # Fallback to fetching simulated or live position from provider
            vessel_res = await db.execute(select(Vessel).where(Vessel.id == vessel_id))
            vessel = vessel_res.scalar_one_or_none()
            if vessel:
                provider = cls.get_provider()
                provider_data = await provider.get_vessel_position(vessel.imo_number)
                if provider_data:
                    return AISPositionResponse(
                        id=0,
                        vessel_id=vessel_id,
                        timestamp=provider_data["timestamp"],
                        latitude=provider_data["latitude"],
                        longitude=provider_data["longitude"],
                        speed=provider_data.get("speed"),
                        course=provider_data.get("course"),
                        heading=provider_data.get("heading"),
                        destination=provider_data.get("destination"),
                        eta=provider_data.get("eta"),
                        navigation_status=provider_data.get("navigation_status"),
                    )
            return None
        return AISPositionResponse.model_validate(pos)

    @classmethod
    async def get_vessel_track(
        cls, db: AsyncSession, vessel_id: int, limit: int = 50
    ) -> VesselTrackResponse:
        vessel_res = await db.execute(select(Vessel).where(Vessel.id == vessel_id))
        vessel = vessel_res.scalar_one_or_none()
        if vessel is None:
            raise NotFoundException("Vessel", vessel_id)

        result = await db.execute(
            select(AISPosition)
            .where(AISPosition.vessel_id == vessel_id)
            .order_by(AISPosition.timestamp.desc())
            .limit(limit)
        )
        positions = result.scalars().all()

        if not positions:
            # Check provider for simulated track
            provider = cls.get_provider()
            track_data = await provider.get_vessel_track(vessel.imo_number)
            pos_responses = [
                AISPositionResponse(
                    id=idx + 1,
                    vessel_id=vessel_id,
                    timestamp=t["timestamp"],
                    latitude=t["latitude"],
                    longitude=t["longitude"],
                    speed=t.get("speed"),
                    course=t.get("course"),
                    heading=t.get("heading"),
                )
                for idx, t in enumerate(track_data)
            ]
            return VesselTrackResponse(
                vessel_id=vessel_id,
                positions=pos_responses,
                total_positions=len(pos_responses),
            )

        pos_responses = [AISPositionResponse.model_validate(p) for p in positions]
        return VesselTrackResponse(
            vessel_id=vessel_id,
            positions=pos_responses,
            total_positions=len(pos_responses),
        )
