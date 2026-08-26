# SIH26006 — Intelligent Freight Forecasting & Vessel Chartering Platform Backend

A production-grade, asynchronous Python backend connecting Procurement Officers, Ship Owners, and Port Owners with AI/ML freight rate forecasting, AIS vessel tracking, PostGIS spatial services, port congestion prediction, and automated charter optimization.

---

## Table of Contents

1. [Core Platform Mission](#1-core-platform-mission)
2. [Technology Stack](#2-technology-stack)
3. [Architecture Overview](#3-architecture-overview)
4. [Environment Setup & Installation](#4-environment-setup--installation)
5. [Database & PostGIS Setup](#5-database--postgis-setup)
6. [Running the Application](#6-running-the-application)
7. [Running Automated Tests](#7-running-automated-tests)
8. [Docker Compose Deployment](#8-docker-compose-deployment)
9. [API Documentation & Endpoints](#9-api-documentation--endpoints)
10. [WebSockets & Real-Time Telemetry](#10-websockets--real-time-telemetry)
11. [Background Tasks (Celery + Redis)](#11-background-tasks-celery--redis)
12. [Team Integration Contracts](#12-team-integration-contracts)
13. [Security Architecture & Best Practices](#13-security-architecture--best-practices)

---

## 1. Core Platform Mission

The SIH26006 backend is not a loose set of disconnected CRUD APIs. It connects:

$$\text{AIS Tracking} + \text{GIS / PostGIS} + \text{Freight Data} + \text{Weather} + \text{ML Forecasting} + \text{Congestion Prediction} + \text{Vessel Constraints} \longrightarrow \text{Optimization Engine}$$

The system directly answers:
> **"Which vessel should we charter, at what freight rate, and when should we charter it?"**

---

## 2. Technology Stack

- **Runtime**: Python 3.12+
- **API Framework**: FastAPI (Async)
- **ASGI Server**: Uvicorn
- **Database**: PostgreSQL 16 with PostGIS 3.4
- **ORM & Migrations**: SQLAlchemy 2.0 (Async with `asyncpg`, sync with `psycopg2` for Alembic)
- **Spatial ORM**: GeoAlchemy2 & Shapely
- **Authentication**: JWT (RS256 / HS256) with OAuth2 Bearer Tokens & Password Hashing (Bcrypt)
- **Validation**: Pydantic v2 & Pydantic Settings
- **Task Queue**: Celery with Redis broker and Celery Beat scheduler
- **Cache & Pub/Sub**: Redis 7
- **AI/ML Engine**: Scikit-Learn, XGBoost, Joblib, NumPy, Pandas
- **Testing**: Pytest, Pytest-Asyncio, Pytest-Cov, HTTPX, AIOSQLite
- **Containerization**: Docker & Docker Compose

---

## 3. Architecture Overview

```
backend/
├── app/
│   ├── main.py                     # FastAPI app factory, CORS, exception handlers
│   ├── core/
│   │   ├── config.py               # Pydantic Settings configuration from .env
│   │   ├── database.py             # Async SQLAlchemy engine & session factory
│   │   ├── security.py             # Bcrypt hashing & JWT token encode/decode
│   │   └── dependencies.py         # OAuth2 auth dependencies & RBAC role checker
│   ├── models/                     # 18 SQLAlchemy PostGIS models
│   │   ├── user.py, ship_owner.py, port.py, berth.py, vessel.py, ...
│   ├── schemas/                    # Pydantic request/response schemas
│   ├── services/                   # Business logic layer (Repository/Service pattern)
│   │   ├── vessel_service.py       # Vessel inventory & spatial queries
│   │   ├── port_service.py         # Port management & berth allocations
│   │   ├── charter_service.py      # Requirements, requests, offers, contracts
│   │   ├── ais_service.py          # Pluggable AIS provider interface (Mock/Live)
│   │   ├── freight_service.py      # Market rate history & bunker fuel index
│   │   ├── congestion_service.py   # Port queues & congestion prediction
│   │   ├── forecast_service.py     # ML inference execution
│   │   ├── optimization_service.py # Core decision & multi-factor scoring engine
│   │   └── notification_service.py # Notification dispatch & user alerts
│   ├── ml/                         # ML inference infrastructure (Model versioning)
│   │   ├── model_loader.py         # Joblib model loader with cache
│   │   ├── forecasting.py          # Freight rate prediction & confidence bounds
│   │   └── congestion.py           # Port waiting time & utilization predictor
│   ├── tasks/                      # Celery async tasks & cron schedules
│   │   ├── celery_app.py           # Celery configuration & beat schedule
│   │   ├── ais_tasks.py            # AIS telemetry sync task
│   │   ├── weather_tasks.py        # Maritime weather sync task
│   │   └── forecast_tasks.py       # Daily batch forecast task
│   ├── utils/                      # Redis client, structured logging, custom errors
│   └── api/
│       └── routes/                 # 15 Route modules under /api/v1
├── alembic/                        # Migration scripts with PostGIS support
├── tests/                          # 10 comprehensive Pytest async test suites
├── scripts/
│   ├── init-db.sql                 # PostGIS extension initialization
│   └── train_mock_models.py        # Baseline ML model training script
├── Dockerfile                      # Production multi-stage Dockerfile
├── docker-compose.yml              # Backend, Postgres+PostGIS, Redis, Celery services
└── requirements.txt                # Pinned dependencies
```

---

## 4. Environment Setup & Installation

### 1. Clone & Enter Directory
```bash
cd backend
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
Edit `.env` as required (database credentials, secret keys, API keys).

### 3. Create Virtual Environment & Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Train Baseline ML Models
```bash
python scripts/train_mock_models.py
```
This generates versioned model files (`data/models/freight_v1.0.joblib` and `data/models/congestion_v1.0.joblib`).

---

## 5. Database & PostGIS Setup

### Using Docker PostGIS (Recommended)
```bash
docker compose up -d postgres redis
```

### Run Migrations
```bash
alembic upgrade head
```

---

## 6. Running the Application

### Start FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Celery Background Worker
```bash
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
```

### Start Celery Beat Scheduler
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## 7. Running Automated Tests

Run the full async test suite with coverage:
```bash
pytest --cov=app --cov-report=term-missing -v
```

All unit and integration tests run against an isolated in-memory test database with pre-configured role fixtures.

---

## 8. Docker Compose Deployment

To launch the complete infrastructure (FastAPI, PostGIS, Redis, Celery Worker, Celery Beat):

```bash
docker compose up --build
```

Services will be accessible at:
- **API Server & Swagger UI**: `http://localhost:8000/docs`
- **ReDoc UI**: `http://localhost:8000/redoc`
- **PostGIS Database**: `localhost:5432` (`sih26006`)
- **Redis Cache**: `localhost:6379`

---

## 9. API Documentation & Endpoints

All endpoints are versioned under `/api/v1/`:

| Module | Route | Method | Description | Role Required |
|---|---|---|---|---|
| **Auth** | `/api/v1/auth/register` | `POST` | Register user account | Public |
| | `/api/v1/auth/login` | `POST` | OAuth2 Bearer token login | Public |
| | `/api/v1/auth/refresh` | `POST` | Refresh access token | Public |
| | `/api/v1/auth/me` | `GET` | Get current user profile | Authenticated |
| **Vessels** | `/api/v1/vessels` | `GET` | Filter vessels (DWT, draft, type, etc.) | Authenticated |
| | `/api/v1/vessels/available` | `GET` | List available charter vessels | Authenticated |
| | `/api/v1/vessels/near-port/{port_id}` | `GET` | PostGIS spatial search around port | Authenticated |
| | `/api/v1/vessels` | `POST` | Register vessel | SHIP_OWNER, ADMIN |
| **Ports** | `/api/v1/ports` | `GET` | List world ports with spatial data | Authenticated |
| | `/api/v1/ports/{id}/berths` | `GET` | List berths and handling rates | Authenticated |
| | `/api/v1/ports/{id}/congestion` | `GET` | Get latest port congestion metrics | Authenticated |
| **Cargo** | `/api/v1/cargo` | `POST` | Post cargo requirement | PROCUREMENT_OFFICER, ADMIN |
| | `/api/v1/cargo` | `GET` | List cargo requirements | Authenticated |
| **Charters**| `/api/v1/charters/requests` | `POST` | Publish charter request | PROCUREMENT_OFFICER, ADMIN |
| | `/api/v1/charters/offers` | `POST` | Submit charter bid/offer | SHIP_OWNER, ADMIN |
| | `/api/v1/charters/{id}/select-offer` | `POST` | Award offer & generate contract | PROCUREMENT_OFFICER, ADMIN |
| **Optimization** | `/api/v1/optimization/match-vessels` | `POST` | Match & rank candidates | Authenticated |
| | `/api/v1/optimization/recommend` | `POST` | **Unified decision engine** | Authenticated |
| **Forecast** | `/api/v1/forecast/freight` | `GET`/`POST` | AI/ML freight rate prediction | Authenticated |
| **Congestion** | `/api/v1/congestion/predict` | `POST` | Predict port queue & waiting time | Authenticated |
| **AIS** | `/api/v1/ais/vessel/{id}/track` | `GET` | Fetch historical AIS path coordinates | Authenticated |

---

## 10. WebSockets & Real-Time Telemetry

- **Live Vessel Telemetry Stream**: `WS /api/v1/ws/vessels`
  - Real-time stream of vessel positions, heading, speed, and status updates.
- **User Notifications Stream**: `WS /api/v1/ws/notifications?token=<JWT_TOKEN>`
  - Real-time push for charter offers, contract awards, congestion alerts, and rate changes.

---

## 11. Background Tasks (Celery + Redis)

- **AIS Sync** (`sync_ais_positions_task`): Runs every 5 minutes to pull new vessel telemetry.
- **Weather Sync** (`sync_weather_data_task`): Runs hourly to record port and maritime route weather.
- **Batch Forecasts** (`run_scheduled_forecasts_task`): Runs daily at 01:00 UTC to precalculate key global trade route rates.

---

## 12. Team Integration Contracts

### Frontend Engineer
- **Auth**: Pass Bearer token in header: `Authorization: Bearer <access_token>`
- **Docs**: Explore interactive OpenAPI schemas at `/docs`.
- **Response standard**: All responses return `{ success: true, data: {...}, message: "..." }`.
- **Errors**: Standard format `{ success: false, error: { code: "ERROR_CODE", message: "..." } }`.

### AI/ML Engineer
- Place trained models into `data/models/` using naming pattern `<name>_<version>.joblib`.
- Inference interfaces are centralized in `app/ml/forecasting.py` and `app/ml/congestion.py`.
- Model versions are controlled via `FREIGHT_MODEL_VERSION` and `CONGESTION_MODEL_VERSION` in `.env`.

### GIS / AIS Engineer
- Implement custom AIS provider by subclassing `AISProvider` in `app/services/ais_service.py`.
- All vessel positions use EPSG:4326 (`SRID=4326;POINT(lon lat)`).
- Spatial distance calculations use PostGIS Geography casts (`ST_DWithin`, `ST_Distance`).

### Optimization & Logistics Engineer
- Core logic is in `app/services/optimization_service.py`.
- Input parameters: Cargo MT, Origin, Destination Port ID, Preferred Vessel Type, Max Draft, Max Budget.
- Output parameters: Top vessel, Freight rate, Total voyage cost, Congestion risk, Recommended timing window (BOOK_NOW / WAIT), and human-readable explanation.

---

## 13. Security Architecture & Best Practices

1. **Role-Based Access Control (RBAC)**: Strict server-side authorization on every route using `require_role(...)`.
2. **Password Security**: Bcrypt with salt rounds; hashes are never exposed in response schemas.
3. **JWT Expiration & Invalidation**: Short-lived access tokens (30 min) with refresh token rotation.
4. **SQL Injection Protection**: 100% parameterized queries via SQLAlchemy 2.0 ORM.
5. **CORS Whitelisting**: Strict origin matching configurable through `CORS_ORIGINS`.
6. **Input Validation**: Pydantic v2 schemas reject out-of-range coordinates, negative quantities, and invalid drafts.
7. **Rate Limiting**: Sliding window Redis rate limiter utility for public endpoints.
