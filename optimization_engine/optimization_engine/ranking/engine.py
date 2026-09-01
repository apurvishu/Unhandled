"""
Vessel Ranking Engine (Phase 5).

Ranks feasible vessels using six configurable, weighted components:
total voyage cost, deadline buffer, risk, cargo suitability,
availability, and operational suitability.

Architecture:
    - **Hard constraints are absolute.** A vessel rejected by Phase 1
      (matching) or Phase 2 (voyage feasibility) is *never* scored or
      assigned a rank here, no matter how favorable its raw numbers
      might look. This is enforced structurally, not just by
      convention: infeasible vessels never enter the scoring path.
    - **No ML, no OR-Tools.** Ranking is a transparent, deterministic
      weighted-sum of 0-100 component scores.
    - **Consumes, does not recompute, Phase 2/3/4 outputs.** This
      engine takes ``VoyageFeasibilityResult``, ``VoyageCostBreakdown``,
      and ``RiskAssessmentResult`` as inputs; it does not reach into
      matching, economics, or risk internals.
    - **Deterministic.** Identical inputs always produce identical
      scores and an identical order; ties are broken by ``vessel_id``.
"""

from __future__ import annotations

from typing import Optional

from optimization_engine.domain.models import Cargo, VoyageFeasibilityResult
from optimization_engine.economics.models import VoyageCostBreakdown
from optimization_engine.ranking.calculations import (
    calculate_availability_lead_days,
    calculate_availability_score,
    calculate_batch_relative_score,
    calculate_cargo_suitability_score,
    calculate_cargo_utilization_ratio,
    calculate_operational_suitability_score,
    calculate_overall_rank_score,
    calculate_weighted_contribution,
    normalize_weights,
)
from optimization_engine.ranking.models import (
    RankedVessel,
    RankingComponentScore,
    RankingRawMetrics,
    RankingWeights,
)
from optimization_engine.risk.models import RiskAssessmentResult

_BASELINE_ASSUMPTIONS: list[str] = [
    "Cost, risk, and deadline buffer are scored relative to the other "
    "feasible candidates in this batch (best in the batch scores 100); "
    "there is no universal 'good' cost or risk value in isolation.",
    "Cargo suitability, availability, and operational suitability are "
    "scored from each vessel's own properties, independent of other "
    "candidates.",
    "Weights are normalized to sum to 1.0 before being applied, "
    "regardless of the configured raw values.",
    "Ranking never overrides Phase 1/Phase 2 hard feasibility: "
    "infeasible vessels are never scored or ranked.",
    "This module performs no machine learning and uses no mathematical "
    "solver (e.g. OR-Tools); ranking is a transparent weighted sum.",
]


class RankingEngine:
    """Ranks feasible vessels using transparent, configurable weights.

    Usage::

        ranking_engine = RankingEngine()
        ranked = ranking_engine.rank(voyage_results, cost_results, risk_results, cargo)

        top_pick = ranking_engine.feasible(ranked)[0]   # rank == 1
        excluded = ranking_engine.excluded(ranked)      # infeasible vessels
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rank(
        self,
        voyage_results: list[VoyageFeasibilityResult],
        cost_results: list[VoyageCostBreakdown],
        risk_results: list[RiskAssessmentResult],
        cargo: Cargo,
        *,
        weights: Optional[RankingWeights] = None,
    ) -> list[RankedVessel]:
        """Rank vessels from a full set of Phase 2 voyage results.

        Args:
            voyage_results: Phase 2 results for every candidate vessel
                (any mix of feasible and infeasible — this engine does
                the feasible/infeasible split itself).
            cost_results: Phase 3 cost breakdowns for the *feasible*
                vessels in ``voyage_results``. Must contain one entry
                per feasible vessel.
            risk_results: Phase 4 risk assessments for the *feasible*
                vessels in ``voyage_results``. Must contain one entry
                per feasible vessel.
            cargo: The cargo requirement being evaluated.
            weights: Optional configurable component weights. Defaults
                to ``RankingWeights()`` if omitted. Weights are
                normalized internally, so they need not sum to 1.0.

        Returns:
            A list of ``RankedVessel``, ranked (feasible, sorted by
            score) first, followed by excluded (infeasible) vessels.
            Use ``feasible()``/``excluded()`` to split them apart.

        Raises:
            ValueError: If a feasible vessel in ``voyage_results`` has
                no matching entry in ``cost_results`` or
                ``risk_results``. Ranking never fabricates missing
                cost or risk data.
        """
        weights = weights if weights is not None else RankingWeights()

        cost_by_vessel_id = {c.vessel_id: c for c in cost_results}
        risk_by_vessel_id = {r.vessel_id: r for r in risk_results}

        feasible_voyages = [vr for vr in voyage_results if vr.feasible]
        infeasible_voyages = [vr for vr in voyage_results if not vr.feasible]

        excluded_results = [self._build_excluded(vr) for vr in infeasible_voyages]

        if not feasible_voyages:
            return excluded_results

        self._validate_data_present(feasible_voyages, cost_by_vessel_id, risk_by_vessel_id)

        raw = self._collect_raw_metrics(feasible_voyages, cost_by_vessel_id, risk_by_vessel_id, cargo)
        batches = self._compute_batch_bounds(raw)
        normalized_weights = normalize_weights(weights.as_dict())

        scored = [
            self._score_vessel(vr, raw[vr.vessel.vessel_id], batches, normalized_weights)
            for vr in feasible_voyages
        ]

        # Deterministic ordering: best score first; ties broken by vessel_id.
        scored.sort(key=lambda rv: (-rv.overall_score, rv.vessel_id))

        n = len(scored)
        ranked_results = []
        for i, rv in enumerate(scored):
            rv_with_rank = rv.model_copy(
                update={
                    "rank": i + 1,
                    "reasons": [f"Ranked #{i + 1} of {n} feasible vessels."] + rv.reasons,
                }
            )
            ranked_results.append(rv_with_rank)

        return ranked_results + excluded_results

    @staticmethod
    def feasible(ranked_vessels: list[RankedVessel]) -> list[RankedVessel]:
        """Return only feasible (ranked) vessels, already sorted by rank."""
        return sorted(
            (rv for rv in ranked_vessels if rv.feasible),
            key=lambda rv: rv.rank if rv.rank is not None else float("inf"),
        )

    @staticmethod
    def excluded(ranked_vessels: list[RankedVessel]) -> list[RankedVessel]:
        """Return only infeasible (excluded, unranked) vessels."""
        return [rv for rv in ranked_vessels if not rv.feasible]

    # ------------------------------------------------------------------
    # Internal: validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_data_present(
        feasible_voyages: list[VoyageFeasibilityResult],
        cost_by_vessel_id: dict[str, VoyageCostBreakdown],
        risk_by_vessel_id: dict[str, RiskAssessmentResult],
    ) -> None:
        for vr in feasible_voyages:
            vessel_id = vr.vessel.vessel_id
            if vessel_id not in cost_by_vessel_id:
                raise ValueError(
                    f"Missing VoyageCostBreakdown for feasible vessel '{vessel_id}'. "
                    "Ranking never fabricates missing cost data — compute economics "
                    "for every feasible vessel before ranking."
                )
            if vessel_id not in risk_by_vessel_id:
                raise ValueError(
                    f"Missing RiskAssessmentResult for feasible vessel '{vessel_id}'. "
                    "Ranking never fabricates missing risk data — compute risk for "
                    "every feasible vessel before ranking."
                )

    # ------------------------------------------------------------------
    # Internal: raw metric collection
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_raw_metrics(
        feasible_voyages: list[VoyageFeasibilityResult],
        cost_by_vessel_id: dict[str, VoyageCostBreakdown],
        risk_by_vessel_id: dict[str, RiskAssessmentResult],
        cargo: Cargo,
    ) -> dict[str, RankingRawMetrics]:
        raw: dict[str, RankingRawMetrics] = {}
        for vr in feasible_voyages:
            vessel = vr.vessel
            cost = cost_by_vessel_id[vessel.vessel_id]
            risk = risk_by_vessel_id[vessel.vessel_id]

            utilization_ratio = calculate_cargo_utilization_ratio(
                cargo.quantity_mt, vessel.cargo_capacity_mt
            )
            lead_days = calculate_availability_lead_days(
                cargo.required_arrival_date, vessel.available_from
            )

            raw[vessel.vessel_id] = RankingRawMetrics(
                total_cost=cost.total_cost,
                currency=cost.currency,
                cost_per_mt=cost.cost_per_mt,
                deadline_buffer_days=vr.deadline_buffer_days,
                overall_risk_score=risk.overall_risk_score,
                risk_category=risk.risk_category,
                cargo_utilization_ratio=utilization_ratio,
                availability_lead_days=lead_days,
                vessel_status=vessel.status,
            )
        return raw

    # ------------------------------------------------------------------
    # Internal: batch bounds for relative scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_batch_bounds(raw: dict[str, RankingRawMetrics]) -> dict[str, tuple[float, float]]:
        costs = [m.total_cost for m in raw.values()]
        risks = [m.overall_risk_score for m in raw.values()]
        buffers = [m.deadline_buffer_days for m in raw.values()]
        return {
            "cost": (min(costs), max(costs)),
            "risk": (min(risks), max(risks)),
            "deadline_buffer": (min(buffers), max(buffers)),
        }

    # ------------------------------------------------------------------
    # Internal: per-vessel scoring
    # ------------------------------------------------------------------

    def _score_vessel(
        self,
        vr: VoyageFeasibilityResult,
        metrics: RankingRawMetrics,
        batches: dict[str, tuple[float, float]],
        normalized_weights: dict[str, float],
    ) -> RankedVessel:
        vessel = vr.vessel

        cost_min, cost_max = batches["cost"]
        risk_min, risk_max = batches["risk"]
        buffer_min, buffer_max = batches["deadline_buffer"]

        component_raw_scores: dict[str, float] = {
            "cost": calculate_batch_relative_score(
                metrics.total_cost, cost_min, cost_max, higher_is_better=False
            ),
            "risk": calculate_batch_relative_score(
                metrics.overall_risk_score, risk_min, risk_max, higher_is_better=False
            ),
            "deadline_buffer": calculate_batch_relative_score(
                metrics.deadline_buffer_days, buffer_min, buffer_max, higher_is_better=True
            ),
            "cargo_suitability": calculate_cargo_suitability_score(
                metrics.cargo_utilization_ratio
            ),
            "availability": calculate_availability_score(metrics.availability_lead_days),
            "operational_suitability": calculate_operational_suitability_score(
                metrics.vessel_status
            ),
        }

        component_reasons: dict[str, str] = {
            "cost": (
                f"Total cost {metrics.total_cost:,.2f} {metrics.currency} "
                f"(batch range {cost_min:,.2f}-{cost_max:,.2f})."
            ),
            "risk": (
                f"Overall risk {metrics.overall_risk_score:.1f}/100 "
                f"({metrics.risk_category.value}) (batch range {risk_min:.1f}-{risk_max:.1f})."
            ),
            "deadline_buffer": (
                f"Deadline buffer {metrics.deadline_buffer_days:+.2f} days "
                f"(batch range {buffer_min:+.2f} to {buffer_max:+.2f})."
            ),
            "cargo_suitability": (
                f"Cargo uses {metrics.cargo_utilization_ratio * 100:.1f}% of vessel capacity."
            ),
            "availability": (
                f"Vessel available {metrics.availability_lead_days:.1f} days before deadline."
            ),
            "operational_suitability": f"Vessel status: {metrics.vessel_status.value}.",
        }

        component_scores: list[RankingComponentScore] = []
        contributions: list[float] = []
        for name, weight in normalized_weights.items():
            score = component_raw_scores[name]
            contribution = calculate_weighted_contribution(score, weight)
            contributions.append(contribution)
            component_scores.append(
                RankingComponentScore(
                    name=name,
                    normalized_score=score,
                    weight=weight,
                    weighted_contribution=contribution,
                    reason=component_reasons[name],
                )
            )

        overall_score = calculate_overall_rank_score(contributions)
        reasons = self._build_reasons(component_scores)

        return RankedVessel(
            rank=None,  # assigned by rank() after sorting the full batch
            vessel_id=vessel.vessel_id,
            vessel_name=vessel.vessel_name,
            feasible=True,
            overall_score=overall_score,
            component_scores=component_scores,
            raw_metrics=metrics,
            reasons=reasons,
            assumptions=list(_BASELINE_ASSUMPTIONS),
        )

    @staticmethod
    def _build_excluded(vr: VoyageFeasibilityResult) -> RankedVessel:
        """Build a RankedVessel entry for an infeasible vessel.

        Infeasible vessels are always included in the full result set
        for transparency, but are never scored: no rank, no overall
        score, no component scores, no raw metrics.
        """
        reasons = [
            "Excluded from ranking: vessel did not pass Phase 1/Phase 2 feasibility."
        ] + list(vr.reasons)
        return RankedVessel(
            rank=None,
            vessel_id=vr.vessel.vessel_id,
            vessel_name=vr.vessel.vessel_name,
            feasible=False,
            overall_score=None,
            component_scores=[],
            raw_metrics=None,
            reasons=reasons,
            assumptions=[
                "Infeasible vessels are never scored or ranked, regardless of "
                "any individually favorable raw metric."
            ],
        )

    @staticmethod
    def _build_reasons(component_scores: list[RankingComponentScore]) -> list[str]:
        ranked = sorted(component_scores, key=lambda c: c.weighted_contribution, reverse=True)
        reasons = []
        for i, component in enumerate(ranked[:3]):
            label = "Largest contributor" if i == 0 else "Also significant"
            reasons.append(
                f"{label}: {component.name} (score {component.normalized_score:.1f}/100 x "
                f"weight {component.weight:.2f} = {component.weighted_contribution:.1f})."
            )
        return reasons
