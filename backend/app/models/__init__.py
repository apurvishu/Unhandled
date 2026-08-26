"""
SQLAlchemy models for the SIH26006 platform.

Import all models here so Alembic can discover them via Base.metadata.
"""

from app.models.user import User, UserRole  # noqa: F401
from app.models.ship_owner import ShipOwner  # noqa: F401
from app.models.port import Port  # noqa: F401
from app.models.berth import Berth, BerthStatus  # noqa: F401
from app.models.vessel import Vessel, VesselType, VesselStatus  # noqa: F401
from app.models.cargo_requirement import CargoRequirement, CargoStatus  # noqa: F401
from app.models.charter_request import CharterRequest, CharterRequestStatus  # noqa: F401
from app.models.charter_offer import CharterOffer, OfferStatus  # noqa: F401
from app.models.charter_contract import CharterContract, ContractStatus, ContractType  # noqa: F401
from app.models.voyage import Voyage, VoyageStatus  # noqa: F401
from app.models.port_call import PortCall, PortCallStatus  # noqa: F401
from app.models.freight_rate import FreightRate  # noqa: F401
from app.models.commodity_price import CommodityPrice  # noqa: F401
from app.models.fuel_price import FuelPrice  # noqa: F401
from app.models.weather_data import WeatherData  # noqa: F401
from app.models.ais_position import AISPosition  # noqa: F401
from app.models.congestion_data import CongestionData, CongestionLevel  # noqa: F401
from app.models.forecast_result import ForecastResult  # noqa: F401
from app.models.notification import Notification, NotificationType  # noqa: F401
