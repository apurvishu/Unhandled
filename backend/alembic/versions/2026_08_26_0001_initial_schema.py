"""Initial schema migration with 18 tables and PostGIS spatial columns.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-26 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'PORT_OWNER', 'SHIP_OWNER', 'PROCUREMENT_OFFICER', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. ship_owners
    op.create_table(
        'ship_owners',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('contact_information', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_ship_owners_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ship_owners')),
        sa.UniqueConstraint('user_id', name=op.f('uq_ship_owners_user_id'))
    )

    # 3. ports
    op.create_table(
        'ports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('max_draft', sa.Float(), nullable=True),
        sa.Column('max_loa', sa.Float(), nullable=True),
        sa.Column('cargo_capacity', sa.Float(), nullable=True),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ports'))
    )
    op.create_index(op.f('ix_ports_name'), 'ports', ['name'], unique=False)

    # 4. berths
    op.create_table(
        'berths',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('port_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('max_draft', sa.Float(), nullable=True),
        sa.Column('max_loa', sa.Float(), nullable=True),
        sa.Column('cargo_handling_rate', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('AVAILABLE', 'OCCUPIED', 'UNDER_MAINTENANCE', 'RESERVED', name='berthstatus'), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['port_id'], ['ports.id'], name=op.f('fk_berths_port_id_ports'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_berths'))
    )
    op.create_index(op.f('ix_berths_port_id'), 'berths', ['port_id'], unique=False)

    # 5. vessels
    op.create_table(
        'vessels',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('imo_number', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('ship_owner_id', sa.Integer(), nullable=False),
        sa.Column('vessel_type', sa.Enum('PANAMAX', 'SUPRAMAX', 'CAPESIZE', 'OTHER', name='vesseltype'), nullable=False),
        sa.Column('dwt', sa.Float(), nullable=False),
        sa.Column('loa', sa.Float(), nullable=True),
        sa.Column('beam', sa.Float(), nullable=True),
        sa.Column('draft', sa.Float(), nullable=True),
        sa.Column('year_built', sa.Integer(), nullable=True),
        sa.Column('flag', sa.String(length=100), nullable=True),
        sa.Column('availability_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('AVAILABLE', 'EN_ROUTE', 'AT_PORT', 'UNDER_MAINTENANCE', 'LAID_UP', 'CHARTERED', name='vesselstatus'), nullable=False),
        sa.Column('current_position', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['ship_owner_id'], ['ship_owners.id'], name=op.f('fk_vessels_ship_owner_id_ship_owners'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_vessels'))
    )
    op.create_index(op.f('ix_vessels_imo_number'), 'vessels', ['imo_number'], unique=True)
    op.create_index(op.f('ix_vessels_name'), 'vessels', ['name'], unique=False)
    op.create_index(op.f('ix_vessels_ship_owner_id'), 'vessels', ['ship_owner_id'], unique=False)

    # 6. cargo_requirements
    op.create_table(
        'cargo_requirements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('procurement_user_id', sa.Integer(), nullable=False),
        sa.Column('commodity', sa.String(length=255), nullable=False),
        sa.Column('quantity_mt', sa.Float(), nullable=False),
        sa.Column('origin', sa.String(length=255), nullable=False),
        sa.Column('destination_port_id', sa.Integer(), nullable=True),
        sa.Column('required_arrival', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preferred_vessel_type', sa.Enum('PANAMAX', 'SUPRAMAX', 'CAPESIZE', 'OTHER', name='vesseltype'), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'OPEN', 'IN_PROGRESS', 'FULFILLED', 'CANCELLED', name='cargostatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['destination_port_id'], ['ports.id'], name=op.f('fk_cargo_requirements_destination_port_id_ports'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['procurement_user_id'], ['users.id'], name=op.f('fk_cargo_requirements_procurement_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cargo_requirements'))
    )
    op.create_index(op.f('ix_cargo_requirements_destination_port_id'), 'cargo_requirements', ['destination_port_id'], unique=False)
    op.create_index(op.f('ix_cargo_requirements_procurement_user_id'), 'cargo_requirements', ['procurement_user_id'], unique=False)

    # 7. charter_requests
    op.create_table(
        'charter_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cargo_requirement_id', sa.Integer(), nullable=False),
        sa.Column('requested_by', sa.Integer(), nullable=False),
        sa.Column('vessel_type', sa.Enum('PANAMAX', 'SUPRAMAX', 'CAPESIZE', 'OTHER', name='vesseltype'), nullable=True),
        sa.Column('minimum_dwt', sa.Float(), nullable=True),
        sa.Column('maximum_draft', sa.Float(), nullable=True),
        sa.Column('laycan_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('laycan_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('OPEN', 'OFFERS_RECEIVED', 'UNDER_REVIEW', 'AWARDED', 'CANCELLED', 'EXPIRED', name='charterrequeststatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cargo_requirement_id'], ['cargo_requirements.id'], name=op.f('fk_charter_requests_cargo_requirement_id_cargo_requirements'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], name=op.f('fk_charter_requests_requested_by_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_charter_requests'))
    )
    op.create_index(op.f('ix_charter_requests_cargo_requirement_id'), 'charter_requests', ['cargo_requirement_id'], unique=False)
    op.create_index(op.f('ix_charter_requests_requested_by'), 'charter_requests', ['requested_by'], unique=False)

    # 8. charter_offers
    op.create_table(
        'charter_offers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('charter_request_id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('freight_rate', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('estimated_eta', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validity_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXPIRED', name='offerstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['charter_request_id'], ['charter_requests.id'], name=op.f('fk_charter_offers_charter_request_id_charter_requests'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], name=op.f('fk_charter_offers_vessel_id_vessels'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_charter_offers'))
    )
    op.create_index(op.f('ix_charter_offers_charter_request_id'), 'charter_offers', ['charter_request_id'], unique=False)
    op.create_index(op.f('ix_charter_offers_vessel_id'), 'charter_offers', ['vessel_id'], unique=False)

    # 9. charter_contracts
    op.create_table(
        'charter_contracts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('charter_request_id', sa.Integer(), nullable=False),
        sa.Column('selected_offer_id', sa.Integer(), nullable=True),
        sa.Column('contract_type', sa.Enum('VOYAGE_CHARTER', 'TIME_CHARTER', 'BAREBOAT_CHARTER', 'CONTRACT_OF_AFFREIGHTMENT', name='contracttype'), nullable=False),
        sa.Column('agreed_rate', sa.Float(), nullable=False),
        sa.Column('total_value', sa.Float(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'COMPLETED', 'TERMINATED', 'DISPUTED', name='contractstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['charter_request_id'], ['charter_requests.id'], name=op.f('fk_charter_contracts_charter_request_id_charter_requests'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_offer_id'], ['charter_offers.id'], name=op.f('fk_charter_contracts_selected_offer_id_charter_offers'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_charter_contracts'))
    )
    op.create_index(op.f('ix_charter_contracts_charter_request_id'), 'charter_contracts', ['charter_request_id'], unique=False)
    op.create_index(op.f('ix_charter_contracts_selected_offer_id'), 'charter_contracts', ['selected_offer_id'], unique=False)

    # 10. voyages
    op.create_table(
        'voyages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('cargo_requirement_id', sa.Integer(), nullable=True),
        sa.Column('origin_port_id', sa.Integer(), nullable=False),
        sa.Column('destination_port_id', sa.Integer(), nullable=False),
        sa.Column('departure_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_arrival', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_arrival', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'DELAYED', name='voyagestatus'), nullable=False),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('actual_cost', sa.Float(), nullable=True),
        sa.Column('route_geometry', geoalchemy2.types.Geometry(geometry_type='LINESTRING', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cargo_requirement_id'], ['cargo_requirements.id'], name=op.f('fk_voyages_cargo_requirement_id_cargo_requirements'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['destination_port_id'], ['ports.id'], name=op.f('fk_voyages_destination_port_id_ports'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['origin_port_id'], ['ports.id'], name=op.f('fk_voyages_origin_port_id_ports'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], name=op.f('fk_voyages_vessel_id_vessels'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_voyages'))
    )
    op.create_index(op.f('ix_voyages_cargo_requirement_id'), 'voyages', ['cargo_requirement_id'], unique=False)
    op.create_index(op.f('ix_voyages_vessel_id'), 'voyages', ['vessel_id'], unique=False)

    # 11. port_calls
    op.create_table(
        'port_calls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('voyage_id', sa.Integer(), nullable=False),
        sa.Column('port_id', sa.Integer(), nullable=False),
        sa.Column('berth_id', sa.Integer(), nullable=True),
        sa.Column('eta', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ata', sa.DateTime(timezone=True), nullable=True),
        sa.Column('etd', sa.DateTime(timezone=True), nullable=True),
        sa.Column('atd', sa.DateTime(timezone=True), nullable=True),
        sa.Column('waiting_time', sa.Float(), nullable=True),
        sa.Column('turnaround_time', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('SCHEDULED', 'WAITING', 'AT_BERTH', 'DEPARTED', 'CANCELLED', name='portcallstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], name=op.f('fk_port_calls_berth_id_berths'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['port_id'], ['ports.id'], name=op.f('fk_port_calls_port_id_ports'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voyage_id'], ['voyages.id'], name=op.f('fk_port_calls_voyage_id_voyages'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_port_calls'))
    )
    op.create_index(op.f('ix_port_calls_port_id'), 'port_calls', ['port_id'], unique=False)
    op.create_index(op.f('ix_port_calls_voyage_id'), 'port_calls', ['voyage_id'], unique=False)

    # 12. freight_rates
    op.create_table(
        'freight_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('origin', sa.String(length=255), nullable=False),
        sa.Column('destination', sa.String(length=255), nullable=False),
        sa.Column('vessel_type', sa.Enum('PANAMAX', 'SUPRAMAX', 'CAPESIZE', 'OTHER', name='vesseltype'), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('rate_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_freight_rates'))
    )
    op.create_index(op.f('ix_freight_rates_destination'), 'freight_rates', ['destination'], unique=False)
    op.create_index(op.f('ix_freight_rates_origin'), 'freight_rates', ['origin'], unique=False)
    op.create_index(op.f('ix_freight_rates_rate_date'), 'freight_rates', ['rate_date'], unique=False)

    # 13. commodity_prices
    op.create_table(
        'commodity_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('commodity', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('price_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_commodity_prices'))
    )
    op.create_index(op.f('ix_commodity_prices_commodity'), 'commodity_prices', ['commodity'], unique=False)
    op.create_index(op.f('ix_commodity_prices_price_date'), 'commodity_prices', ['price_date'], unique=False)

    # 14. fuel_prices
    op.create_table(
        'fuel_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fuel_type', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('port', sa.String(length=255), nullable=True),
        sa.Column('price_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_fuel_prices'))
    )
    op.create_index(op.f('ix_fuel_prices_fuel_type'), 'fuel_prices', ['fuel_type'], unique=False)
    op.create_index(op.f('ix_fuel_prices_price_date'), 'fuel_prices', ['price_date'], unique=False)

    # 15. weather_data
    op.create_table(
        'weather_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('wind_speed', sa.Float(), nullable=True),
        sa.Column('wave_height', sa.Float(), nullable=True),
        sa.Column('precipitation', sa.Float(), nullable=True),
        sa.Column('visibility', sa.Float(), nullable=True),
        sa.Column('weather_condition', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_weather_data'))
    )
    op.create_index(op.f('ix_weather_data_timestamp'), 'weather_data', ['timestamp'], unique=False)

    # 16. ais_positions
    op.create_table(
        'ais_positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('course', sa.Float(), nullable=True),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('destination', sa.String(length=255), nullable=True),
        sa.Column('eta', sa.DateTime(timezone=True), nullable=True),
        sa.Column('navigation_status', sa.String(length=100), nullable=True),
        sa.Column('position', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], name=op.f('fk_ais_positions_vessel_id_vessels'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ais_positions'))
    )
    op.create_index(op.f('ix_ais_positions_timestamp'), 'ais_positions', ['timestamp'], unique=False)
    op.create_index(op.f('ix_ais_positions_vessel_id'), 'ais_positions', ['vessel_id'], unique=False)

    # 17. congestion_data
    op.create_table(
        'congestion_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('port_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('vessels_waiting', sa.Integer(), nullable=True),
        sa.Column('vessels_at_berth', sa.Integer(), nullable=True),
        sa.Column('average_waiting_time', sa.Float(), nullable=True),
        sa.Column('berth_utilization', sa.Float(), nullable=True),
        sa.Column('congestion_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='congestionlevel'), nullable=True),
        sa.Column('predicted_waiting_time', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['port_id'], ['ports.id'], name=op.f('fk_congestion_data_port_id_ports'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_congestion_data'))
    )
    op.create_index(op.f('ix_congestion_data_port_id'), 'congestion_data', ['port_id'], unique=False)
    op.create_index(op.f('ix_congestion_data_timestamp'), 'congestion_data', ['timestamp'], unique=False)

    # 18. forecast_results
    op.create_table(
        'forecast_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('route', sa.String(length=255), nullable=False),
        sa.Column('vessel_type', sa.String(length=50), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('predicted_rate', sa.Float(), nullable=False),
        sa.Column('lower_bound', sa.Float(), nullable=True),
        sa.Column('upper_bound', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_forecast_results'))
    )
    op.create_index(op.f('ix_forecast_results_forecast_date'), 'forecast_results', ['forecast_date'], unique=False)
    op.create_index(op.f('ix_forecast_results_route'), 'forecast_results', ['route'], unique=False)

    # 19. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.Enum('CHARTER_REQUEST', 'CHARTER_OFFER', 'CHARTER_AWARDED', 'VESSEL_ARRIVAL', 'CONGESTION_ALERT', 'FORECAST_UPDATE', 'SYSTEM', 'INFO', name='notificationtype'), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_notifications_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications'))
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('forecast_results')
    op.drop_table('congestion_data')
    op.drop_table('ais_positions')
    op.drop_table('weather_data')
    op.drop_table('fuel_prices')
    op.drop_table('commodity_prices')
    op.drop_table('freight_rates')
    op.drop_table('port_calls')
    op.drop_table('voyages')
    op.drop_table('charter_contracts')
    op.drop_table('charter_offers')
    op.drop_table('charter_requests')
    op.drop_table('cargo_requirements')
    op.drop_table('vessels')
    op.drop_table('berths')
    op.drop_table('ports')
    op.drop_table('ship_owners')
    op.drop_table('users')
