"""
Voyage Risk Engine (Phase 4).

Produces a deterministic, explainable, 0-100 risk assessment for a
vessel on a given voyage, combining ten configurable risk factors
with configurable weights.

Architecture:
    - **Independent module** — does not depend on the economics or
      ranking engines; consumes ``Vessel``/``Cargo``/``Route`` (and,
      optionally, a ``VoyageFeasibilityResult`` for convenience) and
      returns a ``RiskAssessmentResult``.
    - **Data-source agnostic** — every raw factor is a typed input on
      ``RiskFactorInput``. No DB/API/ML calls happen here.
    - **No ML** — where a future ML forecast would supply a value
      (e.g. predicted delay risk from Member 1's model), that field is
      optional; if it is missing, a clearly documented deterministic
      fallback is used and the factor is flagged ``is_estimated=True``.
      A fallback is never presented as a live prediction.
    - **Deterministic** — identical inputs always produce an identical
      ``overall_risk_score`` (only ``evaluated_at`` varies).

This engine does NOT rank or select vessels. That is Phase 5's
responsibility; this module only scores risk.
"""

from __future__ import annotations

from typing import Optional

from optimization_engine.domain.models import (
    Cargo,
    Route,
    Vessel,
    VoyageFeasibilityResult,
)
from optimization_engine.risk.calculations import (
    calculate_cargo_hazard_risk_score,
    calculate_overall_score,
    calculate_predicted_delay_risk_fallback,
    calculate_vessel_age_risk_score,
    calculate_weighted_contribution,
    classify_risk_category,
    normalize_weights,
)
from optimization_engine.risk.models import (
    RiskAssessmentResult,
    RiskFactorInput,
    RiskFactorScore,
    RiskWeights,
)

# ---------------------------------------------------------------------------
# Documented defaults used when data is genuinely missing
# ---------------------------------------------------------------------------

_DEFAULT_AGE_RISK_WHEN_UNKNOWN = 40.0
_DEFAULT_DELAY_RISK_WHEN_NO_BUFFER = 50.0

_BASELINE_ASSUMPTIONS: list[str] = [
    "All raw risk factor inputs are mock/demo values unless explicitly supplied by an external system.",
    "Weights are normalized to sum to 1.0 before being applied, regardless of the configured raw values.",
    "Cargo hazard risk is derived from Cargo.hazardous via a simple two-level rule unless an explicit override is supplied.",
    "This module performs no machine learning; any ML-sourced risk factor (e.g. predicted delay) must be supplied externally as an input.",
]


class RiskEngine:
    """Evaluates deterministic, explainable voyage risk for vessels.

    Usage::

        risk_engine = RiskEngine()

        # Direct use
        result = risk_engine.assess(vessel, cargo, route=route)

        # Convenience: integrate directly with a Phase 2 voyage result
        result = risk_engine.assess_voyage(voyage_result, cargo)

        # Batch, e.g. across all feasible vessels for a cargo
        results = risk_engine.assess_all(voyage_results, cargo)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess(
        self,
        vessel: Vessel,
        cargo: Cargo,
        *,
        route: Optional[Route] = None,
        deadline_buffer_days: Optional[float] = None,
        risk_input: Optional[RiskFactorInput] = None,
        weights: Optional[RiskWeights] = None,
    ) -> RiskAssessmentResult:
        """Assess risk for a single vessel/cargo/route combination.

        Args:
            vessel: The candidate vessel.
            cargo: The cargo requirement.
            route: Optional route (used only to record ``route_id`` on
                the result; no route discovery happens here).
            deadline_buffer_days: Optional deadline buffer from a
                Phase 2 voyage feasibility result, used as a fallback
                input for predicted delay risk when no ML forecast is
                supplied. Ignored if ``risk_input.predicted_delay_risk_score``
                is provided.
            risk_input: Configurable raw risk factor inputs. Defaults
                to ``RiskFactorInput()`` (all mock defaults) if omitted.
            weights: Configurable factor weights. Defaults to
                ``RiskWeights()`` if omitted. Weights are normalized
                internally, so they need not sum to 1.0.

        Returns:
            A fully explained ``RiskAssessmentResult``.
        """
        risk_input = risk_input if risk_input is not None else RiskFactorInput()
        weights = weights if weights is not None else RiskWeights()

        raw_scores, reasons_by_factor, estimated_by_factor = self._score_factors(
            vessel=vessel,
            cargo=cargo,
            risk_input=risk_input,
            deadline_buffer_days=deadline_buffer_days,
        )

        normalized_weights = normalize_weights(weights.as_dict())

        factor_scores: list[RiskFactorScore] = []
        contributions: list[float] = []
        for name, normalized_weight in normalized_weights.items():
            raw_score = raw_scores[name]
            contribution = calculate_weighted_contribution(raw_score, normalized_weight)
            contributions.append(contribution)
            factor_scores.append(
                RiskFactorScore(
                    name=name,
                    raw_score=raw_score,
                    weight=normalized_weight,
                    weighted_contribution=contribution,
                    is_estimated=estimated_by_factor[name],
                    reason=reasons_by_factor[name],
                )
            )

        overall_score = calculate_overall_score(contributions)
        category = classify_risk_category(overall_score)

        reasons = self._build_top_level_reasons(overall_score, category, factor_scores)

        assumptions = list(_BASELINE_ASSUMPTIONS)
        if estimated_by_factor["vessel_age"]:
            assumptions.append(
                "vessel_age_years was not supplied; a documented default "
                f"age-risk score of {_DEFAULT_AGE_RISK_WHEN_UNKNOWN:.1f}/100 was used."
            )
        if estimated_by_factor["predicted_delay"]:
            assumptions.append(
                "No external ML delay forecast was supplied; a deterministic "
                "deadline-buffer proxy (or a neutral default if no buffer was "
                "available) was used instead of a real prediction."
            )

        return RiskAssessmentResult(
            vessel_id=vessel.vessel_id,
            vessel_name=vessel.vessel_name,
            cargo_id=cargo.cargo_id,
            route_id=route.route_id if route is not None else None,
            overall_risk_score=overall_score,
            risk_category=category,
            factor_scores=factor_scores,
            reasons=reasons,
            assumptions=assumptions,
        )

    def assess_voyage(
        self,
        voyage_result: VoyageFeasibilityResult,
        cargo: Cargo,
        *,
        risk_input: Optional[RiskFactorInput] = None,
        weights: Optional[RiskWeights] = None,
    ) -> RiskAssessmentResult:
        """Assess risk directly from a Phase 2 voyage feasibility result.

        Convenience wrapper that pulls the vessel, route, and deadline
        buffer straight out of ``voyage_result`` so risk assessment
        integrates cleanly into the matching -> feasibility -> risk
        pipeline.

        Args:
            voyage_result: Phase 2 voyage feasibility result.
            cargo: Cargo requirement.
            risk_input: Optional configurable raw risk inputs.
            weights: Optional configurable factor weights.

        Returns:
            A fully explained ``RiskAssessmentResult``.
        """
        return self.assess(
            vessel=voyage_result.vessel,
            cargo=cargo,
            route=voyage_result.route,
            deadline_buffer_days=voyage_result.deadline_buffer_days,
            risk_input=risk_input,
            weights=weights,
        )

    def assess_all(
        self,
        voyage_results: list[VoyageFeasibilityResult],
        cargo: Cargo,
        *,
        risk_inputs_by_vessel_id: Optional[dict[str, RiskFactorInput]] = None,
        weights: Optional[RiskWeights] = None,
    ) -> list[RiskAssessmentResult]:
        """Assess risk for multiple voyage results.

        Args:
            voyage_results: Phase 2 feasibility results (any mix of
                feasible/infeasible — this engine does not filter).
            cargo: Cargo requirement (same for all vessels in this batch).
            risk_inputs_by_vessel_id: Optional per-vessel overrides,
                keyed by ``vessel_id``. Vessels not present use
                ``RiskFactorInput()`` defaults.
            weights: Optional configurable factor weights, shared
                across the batch.

        Returns:
            A list of ``RiskAssessmentResult`` — one per voyage result.
        """
        risk_inputs_by_vessel_id = risk_inputs_by_vessel_id or {}
        return [
            self.assess_voyage(
                vr,
                cargo,
                risk_input=risk_inputs_by_vessel_id.get(vr.vessel.vessel_id),
                weights=weights,
            )
            for vr in voyage_results
        ]

    # ------------------------------------------------------------------
    # Internal: per-factor raw scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _score_factors(
        vessel: Vessel,
        cargo: Cargo,
        risk_input: RiskFactorInput,
        deadline_buffer_days: Optional[float],
    ) -> tuple[dict[str, float], dict[str, str], dict[str, bool]]:
        """Compute raw 0-100 scores, reasons, and estimation flags per factor.

        Returns three dicts keyed by the same factor names used in
        ``RiskWeights.as_dict()``: raw scores, human-readable reasons,
        and whether a documented fallback (rather than an explicit
        input) was used.
        """
        raw: dict[str, float] = {}
        reasons: dict[str, str] = {}
        estimated: dict[str, bool] = {}

        # ── Weather ──────────────────────────────────────────────────
        raw["weather"] = risk_input.weather_risk_score
        reasons["weather"] = (
            f"Weather risk {risk_input.weather_risk_score:.1f}/100 (mock input)."
        )
        estimated["weather"] = False

        # ── Congestion ───────────────────────────────────────────────
        raw["congestion"] = risk_input.congestion_risk_score
        reasons["congestion"] = (
            f"Congestion risk {risk_input.congestion_risk_score:.1f}/100 (mock input)."
        )
        estimated["congestion"] = False

        # ── Vessel age ───────────────────────────────────────────────
        if risk_input.vessel_age_years is not None:
            age_score = calculate_vessel_age_risk_score(risk_input.vessel_age_years)
            raw["vessel_age"] = age_score
            reasons["vessel_age"] = (
                f"Vessel age {risk_input.vessel_age_years:.1f} years -> "
                f"age risk {age_score:.1f}/100."
            )
            estimated["vessel_age"] = False
        else:
            raw["vessel_age"] = _DEFAULT_AGE_RISK_WHEN_UNKNOWN
            reasons["vessel_age"] = (
                "Vessel age not supplied; assumed default age risk "
                f"{_DEFAULT_AGE_RISK_WHEN_UNKNOWN:.1f}/100."
            )
            estimated["vessel_age"] = True

        # ── Vessel condition / maintenance ──────────────────────────
        raw["vessel_condition"] = risk_input.vessel_condition_score
        reasons["vessel_condition"] = (
            f"Vessel condition/maintenance risk {risk_input.vessel_condition_score:.1f}/100 "
            "(mock input)."
        )
        estimated["vessel_condition"] = False

        # ── Route hazard / security ─────────────────────────────────
        raw["route_hazard"] = risk_input.route_hazard_score
        reasons["route_hazard"] = (
            f"Route hazard/security risk {risk_input.route_hazard_score:.1f}/100 (mock input)."
        )
        estimated["route_hazard"] = False

        # ── Port restriction ────────────────────────────────────────
        raw["port_restriction"] = risk_input.port_restriction_score
        reasons["port_restriction"] = (
            f"Port restriction risk {risk_input.port_restriction_score:.1f}/100 (mock input)."
        )
        estimated["port_restriction"] = False

        # ── Cargo hazard ─────────────────────────────────────────────
        if risk_input.cargo_hazard_override is not None:
            cargo_score = risk_input.cargo_hazard_override
            reasons["cargo_hazard"] = (
                f"Cargo hazard risk {cargo_score:.1f}/100 (explicit override)."
            )
        else:
            cargo_score = calculate_cargo_hazard_risk_score(cargo.hazardous)
            reasons["cargo_hazard"] = (
                f"Cargo hazard risk derived from cargo.hazardous={cargo.hazardous} "
                f"-> {cargo_score:.1f}/100."
            )
        raw["cargo_hazard"] = cargo_score
        estimated["cargo_hazard"] = False

        # ── Documentation / compliance ───────────────────────────────
        raw["documentation_compliance"] = risk_input.documentation_compliance_score
        reasons["documentation_compliance"] = (
            f"Documentation/compliance risk "
            f"{risk_input.documentation_compliance_score:.1f}/100 (mock input)."
        )
        estimated["documentation_compliance"] = False

        # ── Predicted delay ──────────────────────────────────────────
        if risk_input.predicted_delay_risk_score is not None:
            delay_score = risk_input.predicted_delay_risk_score
            reasons["predicted_delay"] = (
                f"Predicted delay risk {delay_score:.1f}/100 (external ML forecast input)."
            )
            estimated["predicted_delay"] = False
        elif deadline_buffer_days is not None:
            delay_score = calculate_predicted_delay_risk_fallback(deadline_buffer_days)
            reasons["predicted_delay"] = (
                "No ML delay forecast supplied; deterministic proxy from deadline "
                f"buffer ({deadline_buffer_days:+.2f} days) -> {delay_score:.1f}/100 "
                "(estimate, not a prediction)."
            )
            estimated["predicted_delay"] = True
        else:
            delay_score = _DEFAULT_DELAY_RISK_WHEN_NO_BUFFER
            reasons["predicted_delay"] = (
                "No ML delay forecast and no deadline buffer supplied; assumed "
                f"neutral default delay risk {_DEFAULT_DELAY_RISK_WHEN_NO_BUFFER:.1f}/100."
            )
            estimated["predicted_delay"] = True
        raw["predicted_delay"] = delay_score

        # ── Historical incidents ─────────────────────────────────────
        raw["historical_incident"] = risk_input.historical_incident_score
        reasons["historical_incident"] = (
            f"Historical incident risk {risk_input.historical_incident_score:.1f}/100 "
            "(mock input)."
        )
        estimated["historical_incident"] = False

        return raw, reasons, estimated

    # ------------------------------------------------------------------
    # Internal: explanation
    # ------------------------------------------------------------------

    @staticmethod
    def _build_top_level_reasons(
        overall_score: float,
        category,
        factor_scores: list[RiskFactorScore],
    ) -> list[str]:
        """Build human-readable, calculation-grounded top-level reasons."""
        reasons = [
            f"Overall risk score {overall_score:.1f}/100 ({category.value.upper()})."
        ]

        ranked = sorted(factor_scores, key=lambda f: f.weighted_contribution, reverse=True)
        for i, factor in enumerate(ranked[:3]):
            label = "Largest contributor" if i == 0 else "Also significant"
            reasons.append(
                f"{label}: {factor.name} (raw {factor.raw_score:.1f}/100 x "
                f"weight {factor.weight:.2f} = {factor.weighted_contribution:.1f})."
            )

        return reasons
