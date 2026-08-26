"""
Optimization and Vessel Matching Engine.

Connects:
AIS + GIS + PostGIS + Freight Data + Weather + ML Forecasting +
Congestion Prediction + Vessel Constraints
into ONE unified decision-making system.
"""

from datetime import datetime, timedelta, timezone
import math
from typing import Any

from geoalchemy2.shape import to_shape
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.congestion import CongestionPredictor
from app.ml.forecasting import FreightForecaster
from app.models.congestion_data import CongestionLevel
from app.models.port import Port
from app.models.vessel import Vessel, VesselStatus, VesselType
from app.schemas.freight import FreightForecastRequest
from app.schemas.optimization import (
    OptimizationRecommendation,
    VesselMatchRequest,
    VesselMatchResponse,
    VesselMatchResult,
)
from app.services.ais_service import AISService
from app.services.forecast_service import ForecastService
from app.services.freight_service import FreightService
from app.services.port_service import PortService
from app.utils.errors import NotFoundException
from app.utils.logging import get_logger

logger = get_logger("optimization_engine")


class OptimizationService:
    @staticmethod
    def _calculate_haversine_distance_nm(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate great circle distance between two points in nautical miles."""
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(3440.065 * c, 1)

    @classmethod
    async def match_and_rank_vessels(
        cls, db: AsyncSession, req: VesselMatchRequest
    ) -> VesselMatchResponse:
        """
        Evaluate all candidate vessels against constraints and rank them by suitability score.
        """
        # 1. Fetch Destination Port constraints
        port = await PortService.get_port_by_id(db, req.destination_port_id)
        port_max_draft = port.max_draft or 99.0
        port_max_loa = port.max_loa or 999.0

        # Effective max draft allowed
        effective_max_draft = min(
            port_max_draft,
            req.max_draft if req.max_draft is not None else 99.0,
        )

        # 2. Query Candidate Vessels
        query = select(Vessel).where(
            and_(
                Vessel.status == VesselStatus.AVAILABLE,
                Vessel.dwt >= req.cargo_quantity_mt * 0.90,  # Capable of carrying cargo
            )
        )
        if req.preferred_vessel_type:
            query = query.where(Vessel.vessel_type == req.preferred_vessel_type)

        result = await db.execute(query)
        candidates = result.scalars().all()

        # 3. Fetch Context: ML Forecast + Port Congestion + Fuel Price
        v_type = req.preferred_vessel_type or (
            VesselType.CAPESIZE
            if req.cargo_quantity_mt >= 100000
            else (VesselType.PANAMAX if req.cargo_quantity_mt >= 60000 else VesselType.SUPRAMAX)
        )

        # Freight Forecast
        forecast = await ForecastService.generate_freight_forecast(
            db,
            FreightForecastRequest(
                origin=req.origin,
                destination=port.name,
                vessel_type=v_type,
                forecast_horizon_days=30,
            ),
        )

        # Congestion Prediction
        congestion_pred = CongestionPredictor.predict_congestion(
            port_id=port.id, horizon_hours=48
        )

        # Latest Fuel Price
        fuel_price = await FreightService.get_latest_fuel_price(db) or 620.0  # USD/MT

        # 4. Evaluate & Score Candidates
        ranked_matches: list[VesselMatchResult] = []

        for v in candidates:
            # Check draft restriction
            if v.draft and v.draft > effective_max_draft:
                continue  # Exceeds port or requested draft

            # Check LOA restriction
            if v.loa and v.loa > port_max_loa:
                continue  # Exceeds port berth LOA

            # Spatial Distance & ETA Calculation
            v_lat, v_lon = port.latitude, port.longitude
            dist_nm = 500.0  # default baseline
            if v.current_position is not None:
                try:
                    pt = to_shape(v.current_position)
                    v_lon, v_lat = float(pt.x), float(pt.y)
                    dist_nm = cls._calculate_haversine_distance_nm(
                        v_lat, v_lon, port.latitude, port.longitude
                    )
                except Exception:
                    pass

            # Calculate ETA: assume average speed of 13 knots
            sailing_hours = dist_nm / 13.0
            eta = datetime.now(timezone.utc) + timedelta(hours=sailing_hours)

            # Cost Calculations
            # Base freight cost = cargo quantity * forecast rate
            freight_cost = req.cargo_quantity_mt * forecast.predicted_rate
            # Fuel cost = (distance / 24 * 13) * 25 MT/day * fuel_price
            fuel_cost = (sailing_hours / 24.0) * 25.0 * fuel_price
            # Port & waiting cost
            waiting_cost = (congestion_pred.predicted_waiting_time / 24.0) * 15000.0  # $15k/day demurrage
            total_cost = round(freight_cost + fuel_cost + waiting_cost, 2)

            if req.max_budget and total_cost > req.max_budget:
                continue  # Exceeds budget

            # Multi-factor Scoring Algorithm (0 - 100)
            # Factor 1: Capacity utilization (ideal is 90% - 105% of DWT)
            capacity_ratio = req.cargo_quantity_mt / max(1.0, v.dwt)
            if 0.85 <= capacity_ratio <= 1.05:
                cap_score = 35.0
            elif capacity_ratio < 0.85:
                cap_score = max(10.0, 35.0 - (0.85 - capacity_ratio) * 30.0)
            else:
                cap_score = 20.0

            # Factor 2: ETA / Distance score (closer vessel = faster turnaround)
            dist_score = max(5.0, 25.0 - (dist_nm / 1000.0) * 5.0)

            # Factor 3: Draft Safety Margin
            draft_margin = effective_max_draft - (v.draft or 10.0)
            draft_score = min(20.0, max(5.0, draft_margin * 5.0))

            # Factor 4: Congestion risk penalty
            cong_penalty = {
                CongestionLevel.LOW: 0.0,
                CongestionLevel.MEDIUM: 4.0,
                CongestionLevel.HIGH: 10.0,
                CongestionLevel.CRITICAL: 18.0,
            }.get(congestion_pred.congestion_level, 5.0)

            # Factor 5: Vessel Age & Specs
            age = (datetime.now().year - v.year_built) if v.year_built else 10
            spec_score = max(5.0, 20.0 - (age * 0.5))

            final_score = round(
                max(1.0, min(100.0, cap_score + dist_score + draft_score + spec_score - cong_penalty)),
                1,
            )

            ranked_matches.append(
                VesselMatchResult(
                    vessel_id=v.id,
                    vessel_name=v.name,
                    imo_number=v.imo_number,
                    vessel_type=v.vessel_type,
                    dwt=v.dwt,
                    score=final_score,
                    estimated_freight_rate=forecast.predicted_rate,
                    estimated_total_cost=total_cost,
                    estimated_eta=eta,
                    congestion_risk=congestion_pred.congestion_level,
                    distance_nm=dist_nm,
                )
            )

        # Sort by score descending
        ranked_matches.sort(key=lambda x: x.score, reverse=True)

        return VesselMatchResponse(
            matches=ranked_matches,
            total_candidates=len(ranked_matches),
            filters_applied={
                "cargo_quantity_mt": req.cargo_quantity_mt,
                "origin": req.origin,
                "destination_port": port.name,
                "effective_max_draft": effective_max_draft,
                "preferred_vessel_type": req.preferred_vessel_type,
            },
        )

    @classmethod
    async def get_optimization_recommendation(
        cls, db: AsyncSession, req: VesselMatchRequest
    ) -> OptimizationRecommendation:
        """
        Generate full end-to-end charter recommendation answering:
        'Which vessel should we charter, at what freight rate, and when should we charter it?'
        """
        match_resp = await cls.match_and_rank_vessels(db, req)

        if not match_resp.matches:
            # Fallback if no exact match found
            port = await PortService.get_port_by_id(db, req.destination_port_id)
            forecast = await ForecastService.generate_freight_forecast(
                db,
                FreightForecastRequest(
                    origin=req.origin,
                    destination=port.name,
                    vessel_type=req.preferred_vessel_type or VesselType.PANAMAX,
                    forecast_horizon_days=30,
                ),
            )
            return OptimizationRecommendation(
                recommendation="WAIT",
                vessel_id=None,
                vessel_name=None,
                estimated_cost=round(req.cargo_quantity_mt * forecast.predicted_rate, 2),
                freight_rate=forecast.predicted_rate,
                congestion_risk=CongestionLevel.MEDIUM,
                reason="No currently available vessels satisfy all port draft and cargo capacity constraints. Broaden constraints or review pending vessel returns.",
                confidence=0.75,
                alternatives=[],
            )

        top_vessel = match_resp.matches[0]
        alternatives = match_resp.matches[1:4]

        # Forecast analysis for timing
        port = await PortService.get_port_by_id(db, req.destination_port_id)
        forecast = await ForecastService.generate_freight_forecast(
            db,
            FreightForecastRequest(
                origin=req.origin,
                destination=port.name,
                vessel_type=top_vessel.vessel_type,
                forecast_horizon_days=30,
            ),
        )

        now = datetime.now(timezone.utc)
        if forecast.trend == "INCREASING":
            recommendation_action = "BOOK_NOW"
            best_window_start = now
            best_window_end = now + timedelta(days=5)
            reason = (
                f"Charter {top_vessel.vessel_name} immediately. Freight rates are forecasted to increase "
                f"from ${forecast.predicted_rate}/MT over the next 30 days while port congestion at {port.name} "
                f"is currently {top_vessel.congestion_risk.value}."
            )
        elif forecast.trend == "DECREASING":
            recommendation_action = "WAIT"
            best_window_start = now + timedelta(days=10)
            best_window_end = now + timedelta(days=20)
            reason = (
                f"Wait for rate softening. Freight rates on the {req.origin} -> {port.name} route are trending downward. "
                f"Target chartering {top_vessel.vessel_name} in approximately 10 to 15 days."
            )
        else:
            recommendation_action = "BOOK_NOW"
            best_window_start = now
            best_window_end = now + timedelta(days=7)
            reason = (
                f"Stable market conditions. {top_vessel.vessel_name} offers optimal capacity fit ({top_vessel.dwt:.0f} DWT) "
                f"and acceptable draft margins with an ETA of {top_vessel.estimated_eta.strftime('%Y-%m-%d') if top_vessel.estimated_eta else 'TBD'}."
            )

        return OptimizationRecommendation(
            recommendation=recommendation_action,
            vessel_id=top_vessel.vessel_id,
            vessel_name=top_vessel.vessel_name,
            estimated_cost=top_vessel.estimated_total_cost,
            freight_rate=top_vessel.estimated_freight_rate,
            congestion_risk=top_vessel.congestion_risk,
            best_charter_window_start=best_window_start,
            best_charter_window_end=best_window_end,
            reason=reason,
            confidence=forecast.confidence,
            alternatives=alternatives,
        )
