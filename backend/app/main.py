"""
SIH26006 Intelligent Freight Forecasting & Vessel Chartering Platform

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.utils.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.utils.logging import setup_logging, get_logger
from app.utils.redis_client import close_redis, get_redis

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # ===== Startup =====
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Test Redis connection
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis not available: {e} — caching disabled")

    logger.info("Application startup complete")

    yield

    # ===== Shutdown =====
    logger.info("Shutting down application...")
    await close_redis()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Intelligent Freight Forecasting & Vessel Chartering Platform. "
            "Connects procurement officers, ship owners, port owners with "
            "AI/ML forecasting, AIS tracking, GIS/PostGIS services, vessel matching, "
            "and charter optimization into a unified decision-making system."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # ===== CORS Middleware =====
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ===== Exception Handlers =====
    from fastapi import HTTPException
    application.add_exception_handler(AppException, app_exception_handler)
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    application.add_exception_handler(Exception, generic_exception_handler)

    # ===== Include API routers =====
    from app.api.routes import (
        auth,
        users,
        vessels,
        ports,
        berths,
        cargo,
        charters,
        voyages,
        ais,
        freight,
        congestion,
        forecasts,
        optimization,
        notifications,
        websockets,
    )

    api_prefix = "/api/v1"
    application.include_router(auth.router, prefix=api_prefix, tags=["Authentication"])
    application.include_router(users.router, prefix=api_prefix, tags=["Users"])
    application.include_router(vessels.router, prefix=api_prefix, tags=["Vessels"])
    application.include_router(ports.router, prefix=api_prefix, tags=["Ports"])
    application.include_router(berths.router, prefix=api_prefix, tags=["Berths"])
    application.include_router(cargo.router, prefix=api_prefix, tags=["Cargo"])
    application.include_router(charters.router, prefix=api_prefix, tags=["Charters"])
    application.include_router(voyages.router, prefix=api_prefix, tags=["Voyages"])
    application.include_router(ais.router, prefix=api_prefix, tags=["AIS"])
    application.include_router(freight.router, prefix=api_prefix, tags=["Freight"])
    application.include_router(congestion.router, prefix=api_prefix, tags=["Congestion"])
    application.include_router(forecasts.router, prefix=api_prefix, tags=["Forecasts"])
    application.include_router(optimization.router, prefix=api_prefix, tags=["Optimization"])
    application.include_router(notifications.router, prefix=api_prefix, tags=["Notifications"])
    application.include_router(websockets.router, prefix=api_prefix, tags=["WebSockets"])

    # ===== Health Check =====
    @application.get("/api/v1/health", tags=["Health"])
    async def health_check():
        return {
            "success": True,
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    return application


app = create_app()
