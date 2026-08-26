"""Port and Berth service for port operations and spatial management."""

from datetime import datetime, timezone
from typing import Sequence

from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.berth import Berth, BerthStatus
from app.models.congestion_data import CongestionData
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.vessel import Vessel
from app.schemas.berth import BerthCreate, BerthResponse, BerthUpdate
from app.schemas.congestion import CongestionDataResponse
from app.schemas.port import PortCreate, PortResponse, PortUpdate
from app.utils.errors import NotFoundException


class PortService:
    @staticmethod
    def _port_to_response(port: Port) -> PortResponse:
        return PortResponse(
            id=port.id,
            name=port.name,
            country=port.country,
            latitude=port.latitude,
            longitude=port.longitude,
            max_draft=port.max_draft,
            max_loa=port.max_loa,
            cargo_capacity=port.cargo_capacity,
            created_at=port.created_at,
        )

    @staticmethod
    def _berth_to_response(berth: Berth) -> BerthResponse:
        return BerthResponse(
            id=berth.id,
            port_id=berth.port_id,
            name=berth.name,
            max_draft=berth.max_draft,
            max_loa=berth.max_loa,
            cargo_handling_rate=berth.cargo_handling_rate,
            status=berth.status,
            created_at=berth.created_at,
        )

    # ===== Port CRUD =====

    @classmethod
    async def create_port(cls, db: AsyncSession, port_in: PortCreate) -> PortResponse:
        geom = WKTElement(f"POINT({port_in.longitude} {port_in.latitude})", srid=4326)
        port = Port(
            name=port_in.name,
            country=port_in.country,
            latitude=port_in.latitude,
            longitude=port_in.longitude,
            max_draft=port_in.max_draft,
            max_loa=port_in.max_loa,
            cargo_capacity=port_in.cargo_capacity,
            geometry=geom,
            created_at=datetime.now(timezone.utc),
        )
        db.add(port)
        await db.flush()
        await db.refresh(port)
        return cls._port_to_response(port)

    @classmethod
    async def get_port_by_id(cls, db: AsyncSession, port_id: int) -> Port:
        result = await db.execute(select(Port).where(Port.id == port_id))
        port = result.scalar_one_or_none()
        if port is None:
            raise NotFoundException("Port", port_id)
        return port

    @classmethod
    async def get_port(cls, db: AsyncSession, port_id: int) -> PortResponse:
        port = await cls.get_port_by_id(db, port_id)
        return cls._port_to_response(port)

    @classmethod
    async def list_ports(
        cls, db: AsyncSession, country: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[PortResponse]:
        query = select(Port)
        if country:
            query = query.where(Port.country.ilike(f"%{country}%"))
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        ports = result.scalars().all()
        return [cls._port_to_response(p) for p in ports]

    @classmethod
    async def update_port(
        cls, db: AsyncSession, port_id: int, port_update: PortUpdate
    ) -> PortResponse:
        port = await cls.get_port_by_id(db, port_id)
        update_data = port_update.model_dump(exclude_unset=True)

        if "latitude" in update_data or "longitude" in update_data:
            lat = update_data.get("latitude", port.latitude)
            lon = update_data.get("longitude", port.longitude)
            port.geometry = WKTElement(f"POINT({lon} {lat})", srid=4326)

        for field, value in update_data.items():
            setattr(port, field, value)

        await db.flush()
        await db.refresh(port)
        return cls._port_to_response(port)

    # ===== Berth Management =====

    @classmethod
    async def create_berth(
        cls, db: AsyncSession, port_id: int, berth_in: BerthCreate
    ) -> BerthResponse:
        await cls.get_port_by_id(db, port_id)  # Validate port exists

        geom = None
        if berth_in.latitude is not None and berth_in.longitude is not None:
            geom = WKTElement(f"POINT({berth_in.longitude} {berth_in.latitude})", srid=4326)

        berth = Berth(
            port_id=port_id,
            name=berth_in.name,
            max_draft=berth_in.max_draft,
            max_loa=berth_in.max_loa,
            cargo_handling_rate=berth_in.cargo_handling_rate,
            status=berth_in.status,
            geometry=geom,
            created_at=datetime.now(timezone.utc),
        )
        db.add(berth)
        await db.flush()
        await db.refresh(berth)
        return cls._berth_to_response(berth)

    @classmethod
    async def get_berths_for_port(cls, db: AsyncSession, port_id: int) -> list[BerthResponse]:
        await cls.get_port_by_id(db, port_id)
        result = await db.execute(select(Berth).where(Berth.port_id == port_id))
        berths = result.scalars().all()
        return [cls._berth_to_response(b) for b in berths]

    @classmethod
    async def update_berth(
        cls, db: AsyncSession, berth_id: int, berth_update: BerthUpdate
    ) -> BerthResponse:
        result = await db.execute(select(Berth).where(Berth.id == berth_id))
        berth = result.scalar_one_or_none()
        if berth is None:
            raise NotFoundException("Berth", berth_id)

        update_data = berth_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(berth, field, value)

        await db.flush()
        await db.refresh(berth)
        return cls._berth_to_response(berth)

    # ===== Port Congestion & Analytics =====

    @classmethod
    async def get_latest_congestion(
        cls, db: AsyncSession, port_id: int
    ) -> CongestionDataResponse | None:
        await cls.get_port_by_id(db, port_id)
        result = await db.execute(
            select(CongestionData)
            .where(CongestionData.port_id == port_id)
            .order_by(CongestionData.timestamp.desc())
            .limit(1)
        )
        data = result.scalar_one_or_none()
        if data is None:
            return None
        return CongestionDataResponse.model_validate(data)

    @classmethod
    async def get_vessels_at_port(cls, db: AsyncSession, port_id: int) -> list[dict]:
        """Get vessels currently recorded as having active port calls at this port."""
        await cls.get_port_by_id(db, port_id)
        stmt = (
            select(PortCall)
            .where(PortCall.port_id == port_id)
            .order_by(PortCall.eta.desc())
            .limit(20)
        )
        result = await db.execute(stmt)
        port_calls = result.scalars().all()
        return [
            {
                "port_call_id": pc.id,
                "voyage_id": pc.voyage_id,
                "berth_id": pc.berth_id,
                "status": pc.status.value if pc.status else None,
                "eta": pc.eta,
                "ata": pc.ata,
                "waiting_time_hours": pc.waiting_time,
            }
            for pc in port_calls
        ]
