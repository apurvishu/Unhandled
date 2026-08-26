"""Charter workflow API routes: requests, offers, awarding, and contracts."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.charter_request import CharterRequestStatus
from app.models.ship_owner import ShipOwner
from app.models.user import User, UserRole
from app.schemas.charter import (
    CharterContractCreate,
    CharterContractResponse,
    CharterOfferCreate,
    CharterOfferResponse,
    CharterRequestCreate,
    CharterRequestResponse,
    OfferSelectionRequest,
)
from app.schemas.common import StandardResponse
from app.services.charter_service import CharterService

router = APIRouter(prefix="/charters")


async def resolve_ship_owner_id(user: User, db: AsyncSession) -> int:
    owner_res = await db.execute(select(ShipOwner).where(ShipOwner.user_id == user.id))
    owner = owner_res.scalar_one_or_none()
    if owner is None:
        new_owner = ShipOwner(user_id=user.id, company_name=f"{user.name} Shipping")
        db.add(new_owner)
        await db.flush()
        return new_owner.id
    return owner.id


@router.post("/requests", response_model=StandardResponse[CharterRequestResponse], status_code=status.HTTP_201_CREATED)
async def create_charter_request(
    request_in: CharterRequestCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    """Publish a charter request to the vessel market."""
    req = await CharterService.create_charter_request(
        db, user_id=current_user.id, request_in=request_in
    )
    return StandardResponse(data=req, message="Charter request created successfully.")


@router.get("/requests", response_model=StandardResponse[list[CharterRequestResponse]])
async def list_charter_requests(
    request_status: CharterRequestStatus | None = None,
    my_requests_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List open charter requests."""
    user_id = current_user.id if my_requests_only else None
    items = await CharterService.list_charter_requests(
        db, user_id=user_id, status=request_status, skip=skip, limit=limit
    )
    return StandardResponse(data=items)


@router.get("/requests/{request_id}", response_model=StandardResponse[CharterRequestResponse])
async def get_charter_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single charter request details."""
    req = await CharterService.get_charter_request(db, request_id)
    return StandardResponse(data=CharterRequestResponse.model_validate(req))


@router.post("/offers", response_model=StandardResponse[CharterOfferResponse], status_code=status.HTTP_201_CREATED)
async def create_charter_offer(
    offer_in: CharterOfferCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SHIP_OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Submit a competitive charter offer for an open request (Ship Owner)."""
    ship_owner_id = await resolve_ship_owner_id(current_user, db)
    offer = await CharterService.create_charter_offer(
        db, ship_owner_id=ship_owner_id, offer_in=offer_in
    )
    return StandardResponse(data=offer, message="Charter offer submitted successfully.")


@router.get("/requests/{request_id}/offers", response_model=StandardResponse[list[CharterOfferResponse]])
async def get_request_offers(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all offers submitted for a charter request."""
    offers = await CharterService.get_offers_for_request(db, request_id)
    return StandardResponse(data=offers)


@router.post("/{request_id}/select-offer", response_model=StandardResponse[CharterContractResponse])
async def select_charter_offer(
    request_id: int,
    selection: OfferSelectionRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    """Select the winning charter offer and generate the charter contract."""
    contract = await CharterService.select_offer_and_create_contract(
        db, user_id=current_user.id, request_id=request_id, offer_id=selection.offer_id
    )
    return StandardResponse(data=contract, message="Offer awarded and contract generated successfully.")


@router.post("/contracts", response_model=StandardResponse[CharterContractResponse], status_code=status.HTTP_201_CREATED)
async def create_charter_contract(
    contract_in: CharterContractCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    """Directly instantiate a charter contract."""
    contract = await CharterService.create_contract(db, contract_in)
    return StandardResponse(data=contract, message="Charter contract finalized successfully.")
