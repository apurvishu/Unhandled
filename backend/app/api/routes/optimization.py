"""Charter Optimization and Vessel Matching API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.optimization import (
    OptimizationRecommendation,
    VesselMatchRequest,
    VesselMatchResponse,
)
from app.services.optimization_service import OptimizationService

router = APIRouter(prefix="/optimization")


@router.post("/match-vessels", response_model=StandardResponse[VesselMatchResponse])
async def match_vessels(
    req: VesselMatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Match and score suitable vessels for a cargo requirement.

    Evaluates:
    - Port draft & LOA constraints
    - Spatial distances & AIS ETA
    - ML freight forecasts
    - Port congestion risk
    - Fuel & demurrage costs
    """
    results = await OptimizationService.match_and_rank_vessels(db, req)
    return StandardResponse(data=results)


@router.post("/recommend", response_model=StandardResponse[OptimizationRecommendation])
async def get_optimization_recommendation(
    req: VesselMatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate unified AI charter decision:
    'Which vessel should we charter, at what freight rate, and when should we charter it?'
    """
    rec = await OptimizationService.get_optimization_recommendation(db, req)
    return StandardResponse(data=rec)
