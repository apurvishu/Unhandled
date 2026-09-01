"""
Multi-Port / Multi-Route Decision Support Engine (Phase 8).

Compares candidate routes supplied as ``RouteCandidate`` objects — this
engine does not discover, generate, or validate routes itself. Each
``RouteCandidate`` is expected to already carry the full Phase 5
ranked-vessel shortlist computed for that route (i.e. the caller has
already run matching -> voyage -> economics -> risk -> ranking once
per candidate route).

Architecture:
    - **Hard constraints are absolute, one level up.** A route with no
      feasible vessel is never scored or ranked — mirroring Phase 5's
      discipline for vessels.
    - **The cheapest route never automatically wins.** Cost is one of
      several weighted, configurable comparison components.
    - **Optional data is dropped, not fabricated.** Congestion and
      emissions are compared only when every feasible route in the
      batch supplies that data; otherwise that component is simply
      excluded from the comparison (its weight is not silently
      redistributed as a fabricated value).
"""

from __future__ import annotations

from typing import Optional

from optimization_engine.domain.models import Cargo
from optimization_engine.multiroute.models import (
    RankedRoute,
    RouteCandidate,
    RouteComponentScore,
    RouteMetrics,
    RouteWeights,
)
from optimization_engine.ranking.calculations import (
    calculate_batch_relative_score,
    calculate_weighted_contribution,
    calculate_overall_rank_score,
    normalize_weights,
)
from optimization_engine.ranking.engine import RankingEngine

_BASELINE_ASSUMPTIONS: list[str] = [
    "This engine does not discover or validate routes; RouteCandidate objects "
    "must be supplied by the caller, each with its own already-computed Phase "
    "5 ranked-vessel shortlist for that route.",
    "Cost, risk, and deadline buffer are scored relative to the other feasible "
    "routes in this batch, exactly as in Phase 5's vessel ranking.",
    "Congestion and emissions are compared only when every feasible route in "
    "the batch supplies that data; otherwise the component is excluded from "
    "the comparison entirely rather than defaulted to a fabricated value.",
    "A route with no feasible vessel is never scored or ranked, regardless of "
    "how favorable any individual metric might be.",
]


class MultiRouteEngine:
    """Compares feasible routes using transparent, configurable weights.

    Usage::

        multi_route_engine = MultiRouteEngine()
        ranked_routes = multi_route_engine.compare(route_candidates, cargo)

        best = multi_route_engine.feasible(ranked_routes)[0]
    """

    def compare(
        self,
        route_candidates: list[RouteCandidate],
        cargo: Cargo,
        *,
        weights: Optional[RouteWeights] = None,
    ) -> list[RankedRoute]:
        """Rank candidate routes by their best feasible vessel's metrics.

        Args:
            route_candidates: One ``RouteCandidate`` per route to compare.
            cargo: The cargo requirement being evaluated (for reference only).
            weights: Optional configurable component weights.

        Returns:
            A list of ``RankedRoute`` — feasible routes ranked first
            (best score first), followed by infeasible routes (never
            scored). Use ``feasible()``/``excluded()`` to split them.
        """
        weights = weights if weights is not None else RouteWeights()

        metrics_by_route_id: dict[str, RouteMetrics] = {}
        excluded: list[RankedRoute] = []
        feasible_candidates: list[RouteCandidate] = []

        for candidate in route_candidates:
            metrics = self._extract_metrics(candidate)
            if metrics is None:
                excluded.append(self._build_excluded(candidate))
                continue
            metrics_by_route_id[candidate.route.route_id] = metrics
            feasible_candidates.append(candidate)

        if not feasible_candidates:
            return excluded

        have_congestion = all(
            metrics_by_route_id[c.route.route_id].congestion_risk_score is not None
            for c in feasible_candidates
        )
        have_emissions = all(
            metrics_by_route_id[c.route.route_id].emissions_co2_kg is not None
            for c in feasible_candidates
        )

        active_weights = weights.as_dict()
        if not have_congestion:
            active_weights.pop("congestion")
        if not have_emissions:
            active_weights.pop("emissions")
        normalized_weights = normalize_weights(active_weights)

        bounds = self._compute_bounds(
            [metrics_by_route_id[c.route.route_id] for c in feasible_candidates],
            have_congestion,
            have_emissions,
        )

        scored = [
            self._score_route(candidate, metrics_by_route_id[candidate.route.route_id], bounds, normalized_weights)
            for candidate in feasible_candidates
        ]
        scored.sort(key=lambda r: (-r.overall_score, r.route.route_id))

        n = len(scored)
        ranked: list[RankedRoute] = []
        for i, r in enumerate(scored):
            ranked.append(
                r.model_copy(
                    update={
                        "rank": i + 1,
                        "reasons": [f"Ranked #{i + 1} of {n} feasible routes."] + r.reasons,
                    }
                )
            )

        return ranked + excluded

    @staticmethod
    def feasible(ranked_routes: list[RankedRoute]) -> list[RankedRoute]:
        """Return only feasible (ranked) routes, sorted by rank."""
        return sorted(
            (r for r in ranked_routes if r.feasible),
            key=lambda r: r.rank if r.rank is not None else float("inf"),
        )

    @staticmethod
    def excluded(ranked_routes: list[RankedRoute]) -> list[RankedRoute]:
        """Return only infeasible (excluded, unranked) routes."""
        return [r for r in ranked_routes if not r.feasible]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_metrics(candidate: RouteCandidate) -> Optional[RouteMetrics]:
        feasible_vessels = RankingEngine.feasible(candidate.ranked_vessels)
        if not feasible_vessels:
            return None
        best = feasible_vessels[0]
        m = best.raw_metrics

        congestion = None
        if candidate.risk_results:
            matching_risk = next(
                (r for r in candidate.risk_results if r.vessel_id == best.vessel_id), None
            )
            if matching_risk is not None:
                factor = next(
                    (f for f in matching_risk.factor_scores if f.name == "congestion"), None
                )
                if factor is not None:
                    congestion = factor.raw_score

        return RouteMetrics(
            route=candidate.route,
            feasible=True,
            best_vessel_id=best.vessel_id,
            best_vessel_name=best.vessel_name,
            deadline_buffer_days=m.deadline_buffer_days,
            total_cost=m.total_cost,
            cost_per_mt=m.cost_per_mt,
            overall_risk_score=m.overall_risk_score,
            risk_category=m.risk_category,
            congestion_risk_score=congestion,
            emissions_co2_kg=candidate.emissions_co2_kg,
            num_feasible_vessels=len(feasible_vessels),
        )

    @staticmethod
    def _compute_bounds(
        metrics_list: list[RouteMetrics], have_congestion: bool, have_emissions: bool
    ) -> dict[str, tuple[float, float]]:
        bounds = {
            "cost": (min(m.total_cost for m in metrics_list), max(m.total_cost for m in metrics_list)),
            "risk": (
                min(m.overall_risk_score for m in metrics_list),
                max(m.overall_risk_score for m in metrics_list),
            ),
            "deadline_buffer": (
                min(m.deadline_buffer_days for m in metrics_list),
                max(m.deadline_buffer_days for m in metrics_list),
            ),
        }
        if have_congestion:
            bounds["congestion"] = (
                min(m.congestion_risk_score for m in metrics_list),
                max(m.congestion_risk_score for m in metrics_list),
            )
        if have_emissions:
            bounds["emissions"] = (
                min(m.emissions_co2_kg for m in metrics_list),
                max(m.emissions_co2_kg for m in metrics_list),
            )
        return bounds

    @staticmethod
    def _score_route(
        candidate: RouteCandidate,
        metrics: RouteMetrics,
        bounds: dict[str, tuple[float, float]],
        normalized_weights: dict[str, float],
    ) -> RankedRoute:
        raw_scores = {
            "cost": calculate_batch_relative_score(metrics.total_cost, *bounds["cost"], higher_is_better=False),
            "risk": calculate_batch_relative_score(metrics.overall_risk_score, *bounds["risk"], higher_is_better=False),
            "deadline_buffer": calculate_batch_relative_score(
                metrics.deadline_buffer_days, *bounds["deadline_buffer"], higher_is_better=True
            ),
        }
        reasons_by_component = {
            "cost": f"Total cost {metrics.total_cost:,.2f} (batch range {bounds['cost'][0]:,.2f}-{bounds['cost'][1]:,.2f}).",
            "risk": f"Overall risk {metrics.overall_risk_score:.1f}/100 (batch range {bounds['risk'][0]:.1f}-{bounds['risk'][1]:.1f}).",
            "deadline_buffer": f"Deadline buffer {metrics.deadline_buffer_days:+.2f} days.",
        }
        if "congestion" in normalized_weights:
            raw_scores["congestion"] = calculate_batch_relative_score(
                metrics.congestion_risk_score, *bounds["congestion"], higher_is_better=False
            )
            reasons_by_component["congestion"] = f"Congestion risk {metrics.congestion_risk_score:.1f}/100."
        if "emissions" in normalized_weights:
            raw_scores["emissions"] = calculate_batch_relative_score(
                metrics.emissions_co2_kg, *bounds["emissions"], higher_is_better=False
            )
            reasons_by_component["emissions"] = f"Emissions {metrics.emissions_co2_kg:,.1f} kg CO2."

        component_scores = []
        contributions = []
        for name, weight in normalized_weights.items():
            score = raw_scores[name]
            contribution = calculate_weighted_contribution(score, weight)
            contributions.append(contribution)
            component_scores.append(
                RouteComponentScore(
                    name=name, normalized_score=score, weight=weight,
                    weighted_contribution=contribution, reason=reasons_by_component[name],
                )
            )

        overall_score = calculate_overall_rank_score(contributions)
        ranked = sorted(component_scores, key=lambda c: c.weighted_contribution, reverse=True)
        reasons = [
            f"{('Largest contributor' if i == 0 else 'Also significant')}: {c.name} "
            f"(score {c.normalized_score:.1f}/100 x weight {c.weight:.2f} = {c.weighted_contribution:.1f})."
            for i, c in enumerate(ranked[:3])
        ]

        return RankedRoute(
            rank=None,
            route=candidate.route,
            feasible=True,
            overall_score=overall_score,
            component_scores=component_scores,
            raw_metrics=metrics,
            reasons=reasons,
            assumptions=list(_BASELINE_ASSUMPTIONS),
        )

    @staticmethod
    def _build_excluded(candidate: RouteCandidate) -> RankedRoute:
        return RankedRoute(
            rank=None,
            route=candidate.route,
            feasible=False,
            overall_score=None,
            component_scores=[],
            raw_metrics=None,
            reasons=[f"Excluded: no feasible vessel available on route '{candidate.route.route_id}'."],
            assumptions=["Routes with no feasible vessel are never scored or ranked."],
        )
