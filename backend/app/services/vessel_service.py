"""Vessel service for managing vessel inventory and spatial operations."""

from datetime import date, datetime, timezone
from typing import Sequence

from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeomFromText, ST_MakePoint, ST_SetSRID, ST_X, ST_Y
from geoalchemy2.shape import to_shape
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.port import Port
from app.models.ship_owner import ShipOwner
from app.models.vessel import Vessel, VesselStatus, VesselType
from app.schemas.vessel import VesselCreate, VesselFilter, VesselResponse, VesselUpdate
from geoalchemy2.elements import WKTElement
from app.utils.errors import ConflictException, ForbiddenException, NotFoundException


class VesselService:
    @staticmethod
    def _vessel_to_response(vessel: Vessel) -> VesselResponse:
        """Convert a Vessel model with PostGIS geometry to VesselResponse schema."""
        lat = None
        lon = None
        if vessel.current_position is not None:
            try:
                shape_pt = to_shape(vessel.current_position)
                lon = float(shape_pt.x)
                lat = float(shape_pt.y)
            except Exception:
                try:
                    import re
                    m = re.search(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", str(vessel.current_position))
                    if m:
                        lon = float(m.group(1))
                        lat = float(m.group(2))
                except Exception:
                    pass

        return VesselResponse(
            id=vessel.id,
            imo_number=vessel.imo_number,
            name=vessel.name,
            ship_owner_id=vessel.ship_owner_id,
            vessel_type=vessel.vessel_type,
            dwt=vessel.dwt,
            loa=vessel.loa,
            beam=vessel.beam,
            draft=vessel.draft,
            year_built=vessel.year_built,
            flag=vessel.flag,
            availability_date=vessel.availability_date,
            status=vessel.status,
            latitude=lat,
            longitude=lon,
            created_at=vessel.created_at,
        )

    @classmethod
    async def create_vessel(
        cls, db: AsyncSession, ship_owner_id: int, vessel_in: VesselCreate
    ) -> VesselResponse:
        # Check if IMO exists
        existing = await db.execute(
            select(Vessel).where(Vessel.imo_number == vessel_in.imo_number)
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictException(f"Vessel with IMO number '{vessel_in.imo_number}' already exists.")

        # Create geometry if coordinates are provided
        pos_geom = None
        if vessel_in.latitude is not None and vessel_in.longitude is not None:
            pos_geom = WKTElement(f"POINT({vessel_in.longitude} {vessel_in.latitude})", srid=4326)

        vessel = Vessel(
            imo_number=vessel_in.imo_number,
            name=vessel_in.name,
            ship_owner_id=ship_owner_id,
            vessel_type=vessel_in.vessel_type,
            dwt=vessel_in.dwt,
            loa=vessel_in.loa,
            beam=vessel_in.beam,
            draft=vessel_in.draft,
            year_built=vessel_in.year_built,
            flag=vessel_in.flag,
            availability_date=vessel_in.availability_date,
            status=VesselStatus.AVAILABLE,
            current_position=pos_geom,
            created_at=datetime.now(timezone.utc),
        )
        db.add(vessel)
        await db.flush()
        await db.refresh(vessel)
        return cls._vessel_to_response(vessel)

    @classmethod
    async def get_vessel_by_id(cls, db: AsyncSession, vessel_id: int) -> Vessel:
        result = await db.execute(select(Vessel).where(Vessel.id == vessel_id))
        vessel = result.scalar_one_or_none()
        if vessel is None:
            raise NotFoundException("Vessel", vessel_id)
        return vessel

    @classmethod
    async def get_vessel(cls, db: AsyncSession, vessel_id: int) -> VesselResponse:
        vessel = await cls.get_vessel_by_id(db, vessel_id)
        return cls._vessel_to_response(vessel)

    @classmethod
    async def list_vessels(
        cls,
        db: AsyncSession,
        filters: VesselFilter | None = None,
        ship_owner_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[VesselResponse]:
        query = select(Vessel)

        if ship_owner_id is not None:
            query = query.where(Vessel.ship_owner_id == ship_owner_id)

        if filters:
            if filters.vessel_type:
                query = query.where(Vessel.vessel_type == filters.vessel_type)
            if filters.min_dwt is not None:
                query = query.where(Vessel.dwt >= filters.min_dwt)
            if filters.max_dwt is not None:
                query = query.where(Vessel.dwt <= filters.max_dwt)
            if filters.max_draft is not None:
                query = query.where(Vessel.draft <= filters.max_draft)
            if filters.status:
                query = query.where(Vessel.status == filters.status)
            if filters.availability_before:
                query = query.where(Vessel.availability_date <= filters.availability_before)
            if filters.flag:
                query = query.where(Vessel.flag == filters.flag)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        vessels = result.scalars().all()
        return [cls._vessel_to_response(v) for v in vessels]

    @classmethod
    async def get_available_vessels(
        cls,
        db: AsyncSession,
        vessel_type: VesselType | None = None,
        min_dwt: float | None = None,
        max_draft: float | None = None,
        available_before: date | None = None,
    ) -> list[VesselResponse]:
        query = select(Vessel).where(Vessel.status == VesselStatus.AVAILABLE)

        if vessel_type:
            query = query.where(Vessel.vessel_type == vessel_type)
        if min_dwt is not None:
            query = query.where(Vessel.dwt >= min_dwt)
        if max_draft is not None:
            query = query.where(or_(Vessel.draft == None, Vessel.draft <= max_draft))
        if available_before is not None:
            query = query.where(
                or_(
                    Vessel.availability_date == None,
                    Vessel.availability_date <= available_before,
                )
            )

        result = await db.execute(query)
        vessels = result.scalars().all()
        return [cls._vessel_to_response(v) for v in vessels]

    @classmethod
    async def update_vessel(
        cls,
        db: AsyncSession,
        vessel_id: int,
        vessel_update: VesselUpdate,
        ship_owner_id: int | None = None,
        is_admin: bool = False,
    ) -> VesselResponse:
        vessel = await cls.get_vessel_by_id(db, vessel_id)

        if not is_admin and ship_owner_id is not None and vessel.ship_owner_id != ship_owner_id:
            raise ForbiddenException("You are not authorized to update this vessel.")

        update_data = vessel_update.model_dump(exclude_unset=True)

        # Handle coordinate updates into PostGIS point
        lat = update_data.pop("latitude", None)
        lon = update_data.pop("longitude", None)
        if lat is not None and lon is not None:
            vessel.current_position = f"SRID=4326;POINT({lon} {lat})"

        for field, value in update_data.items():
            setattr(vessel, field, value)

        await db.flush()
        await db.refresh(vessel)
        return cls._vessel_to_response(vessel)

    @classmethod
    async def delete_vessel(
        cls,
        db: AsyncSession,
        vessel_id: int,
        ship_owner_id: int | None = None,
        is_admin: bool = False,
    ) -> None:
        vessel = await cls.get_vessel_by_id(db, vessel_id)
        if not is_admin and ship_owner_id is not None and vessel.ship_owner_id != ship_owner_id:
            raise ForbiddenException("You are not authorized to delete this vessel.")

        await db.delete(vessel)
        await db.flush()

    @classmethod
    async def get_vessels_near_port(
        cls, db: AsyncSession, port_id: int, radius_nm: float = 50.0
    ) -> list[dict]:
        """Find vessels within radius_nm nautical miles of a given port using PostGIS."""
        port_res = await db.execute(select(Port).where(Port.id == port_id))
        port = port_res.scalar_one_or_none()
        if port is None:
            raise NotFoundException("Port", port_id)

        # 1 nautical mile = 1852 meters
        radius_meters = radius_nm * 1852.0

        # Query vessels with valid position within distance using PostGIS geography cast
        port_point = f"SRID=4326;POINT({port.longitude} {port.latitude})"
        
        stmt = (
            select(
                Vessel,
                func.ST_Distance(
                    func.geography(Vessel.current_position),
                    func.geography(func.ST_GeomFromText(port_point, 4326)),
                ).label("distance_meters"),
            )
            .where(
                and_(
                    Vessel.current_position != None,
                    func.ST_DWithin(
                        func.geography(Vessel.current_position),
                        func.geography(func.ST_GeomFromText(port_point, 4326)),
                        radius_meters,
                    ),
                )
            )
            .order_by("distance_meters")
        )

        try:
            result = await db.execute(stmt)
            rows = result.all()
            output = []
            for vessel, dist_m in rows:
                resp = cls._vessel_to_response(vessel).model_dump()
                resp["distance_nm"] = round(dist_m / 1852.0, 2) if dist_m else 0.0
                output.append(resp)
            return output
        except Exception:
            # Fallback if PostGIS spatial extension isn't running in pure unit-test mock
            # Calculate distance using Haversine formula
            import math

            vessels_res = await db.execute(select(Vessel).where(Vessel.current_position != None))
            all_vessels = vessels_res.scalars().all()
            output = []
            for v in all_vessels:
                v_resp = cls._vessel_to_response(v)
                if v_resp.latitude is not None and v_resp.longitude is not None:
                    # Haversine distance in nm
                    dlat = math.radians(v_resp.latitude - port.latitude)
                    dlon = math.radians(v_resp.longitude - port.longitude)
                    a = (
                        math.sin(dlat / 2) ** 2
                        + math.cos(math.radians(port.latitude))
                        * math.cos(math.radians(v_resp.latitude))
                        * math.sin(dlon / 2) ** 2
                    )
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    dist_nm = 3440.065 * c  # Earth radius in nautical miles
                    if dist_nm <= radius_nm:
                        d = v_resp.model_dump()
                        d["distance_nm"] = round(dist_nm, 2)
                        output.append(d)
            output.sort(key=lambda x: x.get("distance_nm", 0))
            return output
