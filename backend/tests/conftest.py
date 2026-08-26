"""
Pytest configuration and async test fixtures.

Provides test database sessions, API client, and pre-authenticated test users.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import create_app
from app.models.port import Port
from app.models.ship_owner import ShipOwner
from app.models.user import User, UserRole

from sqlalchemy import event

# In-memory SQLite async test database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

@event.listens_for(test_engine.sync_engine, "connect")
def register_sqlite_spatial_functions(dbapi_connection, connection_record):
    """Register dummy SpatiaLite functions so GeoAlchemy2 works on pure SQLite."""
    def noop(*args):
        return None

    def passthrough(val, *args):
        return val

    def geom_from_ewkt(val, *args):
        if val is None:
            return None
        s = str(val)
        if ";" in s:
            s = s.split(";", 1)[1]
        try:
            from shapely import wkt
            import binascii
            geom = wkt.loads(s)
            return geom.wkb_hex
        except Exception:
            return val

    dbapi_connection.create_function("CheckSpatialIndex", -1, noop, deterministic=True)
    dbapi_connection.create_function("InitSpatialMetaData", -1, noop, deterministic=True)
    dbapi_connection.create_function("AddGeometryColumn", -1, noop, deterministic=True)
    dbapi_connection.create_function("DiscardGeometryColumn", -1, noop, deterministic=True)
    dbapi_connection.create_function("RecoverGeometryColumn", -1, noop, deterministic=True)
    dbapi_connection.create_function("DisableSpatialIndex", -1, noop, deterministic=True)
    dbapi_connection.create_function("CreateSpatialIndex", -1, noop, deterministic=True)
    dbapi_connection.create_function("Spatialite_Version", -1, lambda: "5.0", deterministic=True)
    dbapi_connection.create_function("GeomFromEWKT", -1, geom_from_ewkt, deterministic=True)
    dbapi_connection.create_function("GeomFromText", -1, geom_from_ewkt, deterministic=True)
    dbapi_connection.create_function("ST_GeomFromText", -1, geom_from_ewkt, deterministic=True)
    dbapi_connection.create_function("AsEWKB", -1, passthrough, deterministic=True)
    dbapi_connection.create_function("AsBinary", -1, passthrough, deterministic=True)
    dbapi_connection.create_function("ST_AsBinary", -1, passthrough, deterministic=True)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)




@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database for each test function."""
    async with test_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_users(db_session: AsyncSession) -> dict[str, User]:
    """Seed standard test users with each role."""
    pw_hash = get_password_hash("password123")
    now = datetime.now(timezone.utc)

    admin = User(
        name="Admin User",
        email="admin@test.com",
        password_hash=pw_hash,
        role=UserRole.ADMIN,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    procurement = User(
        name="Procurement Officer",
        email="procurement@test.com",
        password_hash=pw_hash,
        role=UserRole.PROCUREMENT_OFFICER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    ship_owner_user = User(
        name="Ship Owner",
        email="shipowner@test.com",
        password_hash=pw_hash,
        role=UserRole.SHIP_OWNER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    port_owner_user = User(
        name="Port Owner",
        email="portowner@test.com",
        password_hash=pw_hash,
        role=UserRole.PORT_OWNER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db_session.add_all([admin, procurement, ship_owner_user, port_owner_user])
    await db_session.flush()

    # Ship owner profile
    owner_profile = ShipOwner(
        user_id=ship_owner_user.id,
        company_name="Oceanic Logistics Fleet",
        created_at=now,
    )
    db_session.add(owner_profile)

    # Seed initial test port
    port = Port(
        name="Port of Singapore",
        country="Singapore",
        latitude=1.290270,
        longitude=103.851959,
        max_draft=18.0,
        max_loa=400.0,
        cargo_capacity=50000000.0,
        created_at=now,
    )
    db_session.add(port)
    await db_session.commit()

    return {
        "admin": admin,
        "procurement": procurement,
        "ship_owner": ship_owner_user,
        "port_owner": port_owner_user,
        "port": port,
        "ship_owner_profile": owner_profile,
    }


def create_auth_headers(user: User) -> dict[str, str]:
    """Generate authorization Bearer header for a given user."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with db dependency override."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
