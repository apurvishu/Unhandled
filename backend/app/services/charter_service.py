"""Charter service orchestrating cargo requirements, charter requests, offers, and contracts."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cargo_requirement import CargoRequirement, CargoStatus
from app.models.charter_contract import CharterContract, ContractStatus, ContractType
from app.models.charter_offer import CharterOffer, OfferStatus
from app.models.charter_request import CharterRequest, CharterRequestStatus
from app.models.vessel import Vessel, VesselStatus
from app.schemas.cargo import CargoCreate, CargoResponse, CargoUpdate
from app.schemas.charter import (
    CharterContractCreate,
    CharterContractResponse,
    CharterOfferCreate,
    CharterOfferResponse,
    CharterRequestCreate,
    CharterRequestResponse,
)
from app.utils.errors import BadRequestException, ForbiddenException, NotFoundException


class CharterService:
    # ===== Cargo Requirements =====

    @classmethod
    async def create_cargo_requirement(
        cls, db: AsyncSession, procurement_user_id: int, cargo_in: CargoCreate
    ) -> CargoResponse:
        cargo = CargoRequirement(
            procurement_user_id=procurement_user_id,
            commodity=cargo_in.commodity,
            quantity_mt=cargo_in.quantity_mt,
            origin=cargo_in.origin,
            destination_port_id=cargo_in.destination_port_id,
            required_arrival=cargo_in.required_arrival,
            preferred_vessel_type=cargo_in.preferred_vessel_type,
            status=CargoStatus.OPEN,
            created_at=datetime.now(timezone.utc),
        )
        db.add(cargo)
        await db.flush()
        await db.refresh(cargo)
        return CargoResponse.model_validate(cargo)

    @classmethod
    async def get_cargo_requirement(
        cls, db: AsyncSession, cargo_id: int
    ) -> CargoRequirement:
        result = await db.execute(
            select(CargoRequirement).where(CargoRequirement.id == cargo_id)
        )
        cargo = result.scalar_one_or_none()
        if cargo is None:
            raise NotFoundException("Cargo requirement", cargo_id)
        return cargo

    @classmethod
    async def list_cargo_requirements(
        cls,
        db: AsyncSession,
        user_id: int | None = None,
        status: CargoStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CargoResponse]:
        query = select(CargoRequirement)
        if user_id is not None:
            query = query.where(CargoRequirement.procurement_user_id == user_id)
        if status is not None:
            query = query.where(CargoRequirement.status == status)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()
        return [CargoResponse.model_validate(c) for c in items]

    @classmethod
    async def update_cargo_requirement(
        cls,
        db: AsyncSession,
        cargo_id: int,
        cargo_update: CargoUpdate,
        user_id: int | None = None,
        is_admin: bool = False,
    ) -> CargoResponse:
        cargo = await cls.get_cargo_requirement(db, cargo_id)
        if not is_admin and user_id is not None and cargo.procurement_user_id != user_id:
            raise ForbiddenException("You are not authorized to edit this cargo requirement.")

        update_data = cargo_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cargo, field, value)

        await db.flush()
        await db.refresh(cargo)
        return CargoResponse.model_validate(cargo)

    @classmethod
    async def delete_cargo_requirement(
        cls,
        db: AsyncSession,
        cargo_id: int,
        user_id: int | None = None,
        is_admin: bool = False,
    ) -> None:
        cargo = await cls.get_cargo_requirement(db, cargo_id)
        if not is_admin and user_id is not None and cargo.procurement_user_id != user_id:
            raise ForbiddenException("You are not authorized to delete this cargo requirement.")
        await db.delete(cargo)
        await db.flush()

    # ===== Charter Requests =====

    @classmethod
    async def create_charter_request(
        cls, db: AsyncSession, user_id: int, request_in: CharterRequestCreate
    ) -> CharterRequestResponse:
        # Verify cargo requirement exists and belongs to user
        cargo = await cls.get_cargo_requirement(db, request_in.cargo_requirement_id)
        if cargo.procurement_user_id != user_id:
            raise ForbiddenException("Cargo requirement does not belong to you.")

        charter_req = CharterRequest(
            cargo_requirement_id=request_in.cargo_requirement_id,
            requested_by=user_id,
            vessel_type=request_in.vessel_type or cargo.preferred_vessel_type,
            minimum_dwt=request_in.minimum_dwt or cargo.quantity_mt,
            maximum_draft=request_in.maximum_draft,
            laycan_start=request_in.laycan_start,
            laycan_end=request_in.laycan_end,
            status=CharterRequestStatus.OPEN,
            created_at=datetime.now(timezone.utc),
        )
        db.add(charter_req)
        await db.flush()
        await db.refresh(charter_req)
        return CharterRequestResponse.model_validate(charter_req)

    @classmethod
    async def get_charter_request(
        cls, db: AsyncSession, request_id: int
    ) -> CharterRequest:
        result = await db.execute(
            select(CharterRequest).where(CharterRequest.id == request_id)
        )
        req = result.scalar_one_or_none()
        if req is None:
            raise NotFoundException("Charter request", request_id)
        return req

    @classmethod
    async def list_charter_requests(
        cls,
        db: AsyncSession,
        user_id: int | None = None,
        status: CharterRequestStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CharterRequestResponse]:
        query = select(CharterRequest)
        if user_id is not None:
            query = query.where(CharterRequest.requested_by == user_id)
        if status is not None:
            query = query.where(CharterRequest.status == status)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()
        return [CharterRequestResponse.model_validate(r) for r in items]

    # ===== Charter Offers =====

    @classmethod
    async def create_charter_offer(
        cls, db: AsyncSession, ship_owner_id: int, offer_in: CharterOfferCreate
    ) -> CharterOfferResponse:
        # Verify charter request exists and is open
        req = await cls.get_charter_request(db, offer_in.charter_request_id)
        if req.status not in (CharterRequestStatus.OPEN, CharterRequestStatus.OFFERS_RECEIVED):
            raise BadRequestException("This charter request is no longer accepting offers.")

        # Verify vessel exists and belongs to ship owner
        vessel_res = await db.execute(
            select(Vessel).where(Vessel.id == offer_in.vessel_id)
        )
        vessel = vessel_res.scalar_one_or_none()
        if vessel is None:
            raise NotFoundException("Vessel", offer_in.vessel_id)
        if vessel.ship_owner_id != ship_owner_id:
            raise ForbiddenException("You do not own this vessel.")

        # Calculate total cost if not provided
        cargo = await cls.get_cargo_requirement(db, req.cargo_requirement_id)
        total_cost = offer_in.total_cost or (offer_in.freight_rate * cargo.quantity_mt)

        offer = CharterOffer(
            charter_request_id=offer_in.charter_request_id,
            vessel_id=offer_in.vessel_id,
            freight_rate=offer_in.freight_rate,
            total_cost=total_cost,
            estimated_eta=offer_in.estimated_eta,
            validity_until=offer_in.validity_until,
            status=OfferStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        db.add(offer)

        # Update request status to OFFERS_RECEIVED
        req.status = CharterRequestStatus.OFFERS_RECEIVED
        await db.flush()
        await db.refresh(offer)
        return CharterOfferResponse.model_validate(offer)

    @classmethod
    async def get_offers_for_request(
        cls, db: AsyncSession, request_id: int
    ) -> list[CharterOfferResponse]:
        await cls.get_charter_request(db, request_id)
        result = await db.execute(
            select(CharterOffer)
            .where(CharterOffer.charter_request_id == request_id)
            .order_by(CharterOffer.freight_rate.asc())
        )
        offers = result.scalars().all()
        return [CharterOfferResponse.model_validate(o) for o in offers]

    # ===== Offer Selection & Contracts =====

    @classmethod
    async def select_offer_and_create_contract(
        cls, db: AsyncSession, user_id: int, request_id: int, offer_id: int
    ) -> CharterContractResponse:
        # Validate charter request
        req = await cls.get_charter_request(db, request_id)
        if req.requested_by != user_id:
            raise ForbiddenException("Only the procurement officer who created this request can award the offer.")

        # Validate offer
        offer_res = await db.execute(
            select(CharterOffer).where(
                CharterOffer.id == offer_id,
                CharterOffer.charter_request_id == request_id,
            )
        )
        offer = offer_res.scalar_one_or_none()
        if offer is None:
            raise NotFoundException("Charter offer", offer_id)

        # Update offer statuses
        offer.status = OfferStatus.ACCEPTED

        # Reject all other offers for this request
        all_offers_res = await db.execute(
            select(CharterOffer).where(
                CharterOffer.charter_request_id == request_id,
                CharterOffer.id != offer_id,
            )
        )
        for other_offer in all_offers_res.scalars().all():
            other_offer.status = OfferStatus.REJECTED

        # Update request status
        req.status = CharterRequestStatus.AWARDED

        # Update vessel status
        vessel_res = await db.execute(
            select(Vessel).where(Vessel.id == offer.vessel_id)
        )
        vessel = vessel_res.scalar_one_or_none()
        if vessel:
            vessel.status = VesselStatus.CHARTERED

        # Create contract
        contract = CharterContract(
            charter_request_id=request_id,
            selected_offer_id=offer_id,
            contract_type=ContractType.VOYAGE_CHARTER,
            agreed_rate=offer.freight_rate,
            total_value=offer.total_cost,
            start_date=datetime.now(timezone.utc),
            status=ContractStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
        db.add(contract)
        await db.flush()
        await db.refresh(contract)
        return CharterContractResponse.model_validate(contract)

    @classmethod
    async def create_contract(
        cls, db: AsyncSession, contract_in: CharterContractCreate
    ) -> CharterContractResponse:
        contract = CharterContract(
            charter_request_id=contract_in.charter_request_id,
            selected_offer_id=contract_in.selected_offer_id,
            contract_type=contract_in.contract_type,
            agreed_rate=contract_in.agreed_rate,
            total_value=contract_in.total_value,
            start_date=contract_in.start_date,
            end_date=contract_in.end_date,
            status=ContractStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
        db.add(contract)
        await db.flush()
        await db.refresh(contract)
        return CharterContractResponse.model_validate(contract)
