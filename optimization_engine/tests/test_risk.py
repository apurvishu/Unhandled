"""
Tests for the voyage risk engine (Phase 4).

Tests cover:
    - Individual risk-factor calculation functions
    - Score bounds (overall score always in [0, 100])
    - Configurable weighting (including non-normalized weights)
    - Invalid inputs (out-of-range factor scores, negative age)
    - Missing inputs (defaults used, factors flagged as estimated)
    - Deterministic behavior (identical inputs -> identical score)
    - Explanations (reasons/assumptions are present and calculation-grounded)
    - Integration with a feasible voyage (Phase 1 -> Phase 2 -> Phase 4)
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from optimization_engine.domain.models import (
    Cargo,
    Route,
    Vessel,
    VesselStatus,
    VoyageFeasibilityResult,
)
from optimization_engine.risk.calculations import (
    calculate_cargo_hazard_risk_score,
    calculate_overall_score,
    calculate_predicted_delay_risk_fallback,
    calculate_vessel_age_risk_score,
    calculate_weighted_contribution,
    classify_risk_category,
    clamp,
    normalize_weights,
)
from optimization_engine.risk.engine import RiskEngine
from optimization_engine.risk.models import (
    RiskAssessmentResult,
    RiskCategory,
    RiskFactorInput,
    RiskWeights,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> RiskEngine:
    return RiskEngine()


@pytest.fixture
def sample_vessel() -> Vessel:
    return Vessel(
        vessel_id="V-RISK-001",
        vessel_name="MV Risk Test",
        imo="IMO7777777",
        mmsi="MMSI777777",
        vessel_type="bulk_carrier",
        dwt_mt=95_000.0,
        cargo_capacity_mt=85_000.0,
        loa_m=250.0,
        beam_m=43.0,
        draft_m=14.0,
        speed_knots=14.5,
        current_location="Singapore Anchorage",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["iron_ore", "coal"],
    )


@pytest.fixture
def sample_cargo() -> Cargo:
    return Cargo(
        cargo_id="TEST-RISK-001",
        cargo_type="iron_ore",
        quantity_mt=75_000.0,
        origin_port="CNSHA",
        destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15),
        hazardous=False,
    )


@pytest.fixture
def sample_route() -> Route:
    return Route(
        route_id="CNSHA-INPRT",
        origin_port_id="CNSHA",
        destination_port_id="INPRT",
        distance_nm=3_450.0,
    )


def _make_voyage_result(vessel: Vessel, route: Route, **overrides) -> VoyageFeasibilityResult:
    """Create a mock VoyageFeasibilityResult for risk-engine integration tests."""
    defaults = dict(
        vessel=vessel,
        route=route,
        estimated_departure=datetime(2026, 8, 1, 0, 0),
        sailing_hours=237.93,
        sailing_days=9.91,
        estimated_arrival=datetime(2026, 8, 10, 21, 56),
        required_arrival=date(2026, 10, 15),
        deadline_buffer_days=65.09,
        deadline_feasible=True,
        phase1_feasible=True,
        feasible=True,
        reasons=[],
        assumptions=["mock"],
    )
    defaults.update(overrides)
    return VoyageFeasibilityResult(**defaults)


# ---------------------------------------------------------------------------
# Pure calculation functions
# ---------------------------------------------------------------------------


class TestClamp:
    def test_within_range_unchanged(self) -> None:
        assert clamp(50.0) == 50.0

    def test_clamps_above_max(self) -> None:
        assert clamp(150.0) == 100.0

    def test_clamps_below_min(self) -> None:
        assert clamp(-10.0) == 0.0

    def test_custom_bounds(self) -> None:
        assert clamp(5.0, lo=10.0, hi=20.0) == 10.0


class TestVesselAgeRisk:
    def test_young_vessel_floor(self) -> None:
        """Age <= 5 years is floored at score 10."""
        assert calculate_vessel_age_risk_score(0.0) == pytest.approx(10.0)
        assert calculate_vessel_age_risk_score(5.0) == pytest.approx(10.0)

    def test_old_vessel_ceiling(self) -> None:
        """Age >= 25 years is capped at score 90."""
        assert calculate_vessel_age_risk_score(25.0) == pytest.approx(90.0)
        assert calculate_vessel_age_risk_score(60.0) == pytest.approx(90.0)

    def test_midpoint_interpolation(self) -> None:
        """Age 15 (midpoint of 5-25) -> score 50 (midpoint of 10-90)."""
        assert calculate_vessel_age_risk_score(15.0) == pytest.approx(50.0)

    def test_monotonically_increasing(self) -> None:
        """Older vessels should never score lower risk than younger ones."""
        ages = [0, 5, 10, 15, 20, 25, 30]
        scores = [calculate_vessel_age_risk_score(a) for a in ages]
        assert scores == sorted(scores)

    def test_negative_age_rejected(self) -> None:
        with pytest.raises(ValueError, match="age_years must be >= 0"):
            calculate_vessel_age_risk_score(-1.0)


class TestCargoHazardRisk:
    def test_hazardous_cargo_scores_higher(self) -> None:
        assert calculate_cargo_hazard_risk_score(True) > calculate_cargo_hazard_risk_score(False)

    def test_non_hazardous_score(self) -> None:
        assert calculate_cargo_hazard_risk_score(False) == pytest.approx(10.0)

    def test_hazardous_score(self) -> None:
        assert calculate_cargo_hazard_risk_score(True) == pytest.approx(65.0)


class TestPredictedDelayFallback:
    def test_on_time_arrival_is_neutral(self) -> None:
        """Zero buffer (arrives exactly on deadline) -> neutral score 50."""
        assert calculate_predicted_delay_risk_fallback(0.0) == pytest.approx(50.0)

    def test_large_buffer_floors_to_zero(self) -> None:
        assert calculate_predicted_delay_risk_fallback(20.0) == pytest.approx(0.0)

    def test_large_lateness_ceilings_to_hundred(self) -> None:
        assert calculate_predicted_delay_risk_fallback(-20.0) == pytest.approx(100.0)

    def test_late_scores_higher_than_early(self) -> None:
        early = calculate_predicted_delay_risk_fallback(5.0)
        late = calculate_predicted_delay_risk_fallback(-5.0)
        assert late > early


class TestWeightNormalization:
    def test_normalizes_to_sum_one(self) -> None:
        result = normalize_weights({"a": 2.0, "b": 2.0})
        assert sum(result.values()) == pytest.approx(1.0)
        assert result == {"a": pytest.approx(0.5), "b": pytest.approx(0.5)}

    def test_already_normalized_unchanged(self) -> None:
        result = normalize_weights({"a": 0.5, "b": 0.5})
        assert result["a"] == pytest.approx(0.5)
        assert result["b"] == pytest.approx(0.5)

    def test_zero_total_weight_rejected(self) -> None:
        with pytest.raises(ValueError, match="Total weight must be > 0"):
            normalize_weights({"a": 0.0, "b": 0.0})

    def test_negative_total_weight_rejected(self) -> None:
        with pytest.raises(ValueError, match="Total weight must be > 0"):
            normalize_weights({"a": -1.0})


class TestOverallScoreAndCategory:
    def test_overall_score_is_sum(self) -> None:
        assert calculate_overall_score([10.0, 20.0, 30.0]) == pytest.approx(60.0)

    def test_overall_score_clamped_at_hundred(self) -> None:
        assert calculate_overall_score([80.0, 80.0]) == pytest.approx(100.0)

    def test_weighted_contribution(self) -> None:
        assert calculate_weighted_contribution(80.0, 0.25) == pytest.approx(20.0)

    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.0, RiskCategory.LOW),
            (24.9, RiskCategory.LOW),
            (25.0, RiskCategory.MODERATE),
            (49.9, RiskCategory.MODERATE),
            (50.0, RiskCategory.HIGH),
            (74.9, RiskCategory.HIGH),
            (75.0, RiskCategory.SEVERE),
            (100.0, RiskCategory.SEVERE),
        ],
    )
    def test_category_thresholds(self, score: float, expected: RiskCategory) -> None:
        assert classify_risk_category(score) == expected


# ---------------------------------------------------------------------------
# Score bounds (engine-level, with extreme configured inputs)
# ---------------------------------------------------------------------------


class TestScoreBounds:
    def test_default_inputs_within_bounds(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        assert 0.0 <= result.overall_risk_score <= 100.0

    def test_all_max_inputs_within_bounds(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        maxed = RiskFactorInput(
            weather_risk_score=100.0,
            congestion_risk_score=100.0,
            vessel_age_years=100.0,
            vessel_condition_score=100.0,
            route_hazard_score=100.0,
            port_restriction_score=100.0,
            cargo_hazard_override=100.0,
            documentation_compliance_score=100.0,
            predicted_delay_risk_score=100.0,
            historical_incident_score=100.0,
        )
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route, risk_input=maxed)
        # vessel_age_years=100 is derived through the age-risk formula, which
        # intentionally caps at 90 (not 100) — no vessel is "absolute max
        # risk" purely from age. Every other factor is a literal 100.
        # Expected: 90*0.10 (vessel_age) + 100*0.90 (remaining weight) = 99.0
        assert result.overall_risk_score == pytest.approx(99.0)
        assert result.risk_category == RiskCategory.SEVERE

    def test_all_zero_inputs_within_bounds(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        zeroed = RiskFactorInput(
            weather_risk_score=0.0,
            congestion_risk_score=0.0,
            vessel_age_years=0.0,
            vessel_condition_score=0.0,
            route_hazard_score=0.0,
            port_restriction_score=0.0,
            cargo_hazard_override=0.0,
            documentation_compliance_score=0.0,
            predicted_delay_risk_score=0.0,
            historical_incident_score=0.0,
        )
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route, risk_input=zeroed)
        # vessel_age_years=0 is derived through the age-risk formula, which
        # intentionally floors at 10 (not 0) — even a brand-new vessel
        # carries a small baseline age risk. Every other factor is a
        # literal 0.
        # Expected: 10*0.10 (vessel_age) + 0*0.90 (remaining weight) = 1.0
        assert result.overall_risk_score == pytest.approx(1.0)
        assert result.risk_category == RiskCategory.LOW

    def test_factor_weights_sum_to_one(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        assert sum(f.weight for f in result.factor_scores) == pytest.approx(1.0)

    def test_contributions_sum_to_overall_score(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        total = sum(f.weighted_contribution for f in result.factor_scores)
        assert total == pytest.approx(result.overall_risk_score)


# ---------------------------------------------------------------------------
# Configurable weighting
# ---------------------------------------------------------------------------


class TestWeighting:
    def test_default_weights_used_when_none_supplied(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        assert len(result.factor_scores) == 10

    def test_custom_weights_change_overall_score(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        risk_input = RiskFactorInput(weather_risk_score=90.0, historical_incident_score=0.0)

        weight_on_weather = RiskWeights(
            weather=1.0, congestion=0, vessel_age=0, vessel_condition=0,
            route_hazard=0, port_restriction=0, cargo_hazard=0,
            documentation_compliance=0, predicted_delay=0, historical_incident=0,
        )
        weight_on_incident = RiskWeights(
            weather=0, congestion=0, vessel_age=0, vessel_condition=0,
            route_hazard=0, port_restriction=0, cargo_hazard=0,
            documentation_compliance=0, predicted_delay=0, historical_incident=1.0,
        )

        result_weather = engine.assess(
            sample_vessel, sample_cargo, route=sample_route,
            risk_input=risk_input, weights=weight_on_weather,
        )
        result_incident = engine.assess(
            sample_vessel, sample_cargo, route=sample_route,
            risk_input=risk_input, weights=weight_on_incident,
        )

        assert result_weather.overall_risk_score == pytest.approx(90.0)
        assert result_incident.overall_risk_score == pytest.approx(0.0)
        assert result_weather.overall_risk_score != result_incident.overall_risk_score

    def test_weights_not_summing_to_one_are_normalized(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        """Weights totalling far more than 1.0 must still yield a score in [0, 100]."""
        heavy_weights = RiskWeights(
            weather=5.0, congestion=5.0, vessel_age=5.0, vessel_condition=5.0,
            route_hazard=5.0, port_restriction=5.0, cargo_hazard=5.0,
            documentation_compliance=5.0, predicted_delay=5.0, historical_incident=5.0,
        )
        result = engine.assess(
            sample_vessel, sample_cargo, route=sample_route, weights=heavy_weights
        )
        assert 0.0 <= result.overall_risk_score <= 100.0
        assert sum(f.weight for f in result.factor_scores) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------


class TestInvalidInputs:
    def test_score_above_hundred_rejected(self) -> None:
        with pytest.raises(ValueError):
            RiskFactorInput(weather_risk_score=150.0)

    def test_negative_score_rejected(self) -> None:
        with pytest.raises(ValueError):
            RiskFactorInput(congestion_risk_score=-5.0)

    def test_negative_vessel_age_rejected(self) -> None:
        with pytest.raises(ValueError):
            RiskFactorInput(vessel_age_years=-2.0)

    def test_negative_weight_rejected(self) -> None:
        with pytest.raises(ValueError):
            RiskWeights(weather=-0.1)


# ---------------------------------------------------------------------------
# Missing inputs
# ---------------------------------------------------------------------------


class TestMissingInputs:
    def test_missing_vessel_age_uses_documented_default(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        age_factor = next(f for f in result.factor_scores if f.name == "vessel_age")
        assert age_factor.is_estimated is True
        assert age_factor.raw_score == pytest.approx(40.0)

    def test_missing_predicted_delay_without_buffer_uses_neutral_default(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        delay_factor = next(f for f in result.factor_scores if f.name == "predicted_delay")
        assert delay_factor.is_estimated is True
        assert delay_factor.raw_score == pytest.approx(50.0)

    def test_missing_predicted_delay_with_buffer_uses_fallback_formula(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(
            sample_vessel, sample_cargo, route=sample_route, deadline_buffer_days=10.0
        )
        delay_factor = next(f for f in result.factor_scores if f.name == "predicted_delay")
        assert delay_factor.is_estimated is True
        assert delay_factor.raw_score == pytest.approx(0.0)

    def test_supplied_predicted_delay_overrides_fallback(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        risk_input = RiskFactorInput(predicted_delay_risk_score=77.0)
        result = engine.assess(
            sample_vessel, sample_cargo, route=sample_route,
            deadline_buffer_days=10.0, risk_input=risk_input,
        )
        delay_factor = next(f for f in result.factor_scores if f.name == "predicted_delay")
        assert delay_factor.is_estimated is False
        assert delay_factor.raw_score == pytest.approx(77.0)

    def test_missing_route_leaves_route_id_none(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo)
        assert result.route_id is None

    def test_cargo_hazard_derived_when_no_override(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_route: Route
    ) -> None:
        hazardous_cargo = Cargo(
            cargo_id="HAZ-001",
            cargo_type="iron_ore",
            quantity_mt=75_000.0,
            origin_port="CNSHA",
            destination_port="INPRT",
            required_arrival_date=date(2026, 10, 15),
            hazardous=True,
        )
        result = engine.assess(sample_vessel, hazardous_cargo, route=sample_route)
        cargo_factor = next(f for f in result.factor_scores if f.name == "cargo_hazard")
        assert cargo_factor.is_estimated is False
        assert cargo_factor.raw_score == pytest.approx(65.0)


# ---------------------------------------------------------------------------
# Deterministic behavior
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_identical_inputs_produce_identical_score(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        r1 = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        r2 = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        assert r1.overall_risk_score == r2.overall_risk_score
        assert r1.risk_category == r2.risk_category
        assert [f.raw_score for f in r1.factor_scores] == [f.raw_score for f in r2.factor_scores]

    def test_identical_inputs_with_explicit_risk_input(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        risk_input = RiskFactorInput(weather_risk_score=42.0, vessel_age_years=12.0)
        r1 = engine.assess(sample_vessel, sample_cargo, route=sample_route, risk_input=risk_input)
        r2 = engine.assess(sample_vessel, sample_cargo, route=sample_route, risk_input=risk_input)
        assert r1.overall_risk_score == pytest.approx(r2.overall_risk_score)


# ---------------------------------------------------------------------------
# Explanations
# ---------------------------------------------------------------------------


class TestExplanations:
    def test_reasons_not_empty(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        assert len(result.reasons) > 0

    def test_top_level_reason_mentions_overall_score(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        assert f"{result.overall_risk_score:.1f}" in result.reasons[0]
        assert result.risk_category.value.upper() in result.reasons[0]

    def test_every_factor_has_a_reason(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        for factor in result.factor_scores:
            assert factor.reason
            assert len(factor.reason) > 0

    def test_assumptions_not_empty(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        assert len(result.assumptions) > 0
        text = " ".join(result.assumptions).lower()
        assert "mock" in text or "estimate" in text or "default" in text

    def test_evaluated_at_populated(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        result = engine.assess(sample_vessel, sample_cargo, route=sample_route)
        assert result.evaluated_at is not None

    def test_explanation_never_contradicts_result(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        """The largest-contributor callout must actually be the largest."""
        risk_input = RiskFactorInput(weather_risk_score=100.0)
        result = engine.assess(
            sample_vessel, sample_cargo, route=sample_route, risk_input=risk_input
        )
        largest = max(result.factor_scores, key=lambda f: f.weighted_contribution)
        assert largest.name in result.reasons[1]


# ---------------------------------------------------------------------------
# Integration with a feasible voyage (Phase 1 -> Phase 2 -> Phase 4)
# ---------------------------------------------------------------------------


class TestVoyageIntegration:
    def test_assess_voyage_matches_manual_assess(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        voyage_result = _make_voyage_result(sample_vessel, sample_route)
        via_voyage = engine.assess_voyage(voyage_result, sample_cargo)
        via_manual = engine.assess(
            sample_vessel,
            sample_cargo,
            route=sample_route,
            deadline_buffer_days=voyage_result.deadline_buffer_days,
        )
        assert via_voyage.overall_risk_score == pytest.approx(via_manual.overall_risk_score)

    def test_large_deadline_buffer_lowers_delay_risk(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        comfortable = _make_voyage_result(sample_vessel, sample_route, deadline_buffer_days=30.0)
        tight = _make_voyage_result(sample_vessel, sample_route, deadline_buffer_days=-5.0)

        result_comfortable = engine.assess_voyage(comfortable, sample_cargo)
        result_tight = engine.assess_voyage(tight, sample_cargo)

        delay_comfortable = next(
            f for f in result_comfortable.factor_scores if f.name == "predicted_delay"
        )
        delay_tight = next(f for f in result_tight.factor_scores if f.name == "predicted_delay")

        assert delay_tight.raw_score > delay_comfortable.raw_score
        assert result_tight.overall_risk_score > result_comfortable.overall_risk_score

    def test_assess_all_matches_per_vessel_assessment(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        voyage_result = _make_voyage_result(sample_vessel, sample_route)
        batch = engine.assess_all([voyage_result], sample_cargo)
        single = engine.assess_voyage(voyage_result, sample_cargo)
        assert len(batch) == 1
        assert batch[0].overall_risk_score == pytest.approx(single.overall_risk_score)

    def test_per_vessel_risk_input_override_in_assess_all(
        self, engine: RiskEngine, sample_vessel: Vessel, sample_cargo: Cargo, sample_route: Route
    ) -> None:
        voyage_result = _make_voyage_result(sample_vessel, sample_route)
        override = RiskFactorInput(weather_risk_score=100.0)
        batch = engine.assess_all(
            [voyage_result],
            sample_cargo,
            risk_inputs_by_vessel_id={sample_vessel.vessel_id: override},
        )
        default_batch = engine.assess_all([voyage_result], sample_cargo)
        assert batch[0].overall_risk_score > default_batch[0].overall_risk_score

    def test_full_pipeline_matching_to_voyage_to_risk(self) -> None:
        """End-to-end: match -> voyage feasibility -> risk, using mock fixtures."""
        from optimization_engine.data.mock.fixtures import (
            MOCK_VESSELS,
            PARADIP,
            ROUTE_LOOKUP,
            SAMPLE_CARGO,
            SHANGHAI,
        )
        from optimization_engine.matching.engine import MatchingEngine
        from optimization_engine.voyage.engine import VoyageFeasibilityEngine

        matching_engine = MatchingEngine()
        match_results = matching_engine.match_vessels(
            SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP
        )
        feasible_matches = matching_engine.feasible(match_results)
        assert len(feasible_matches) > 0

        route = ROUTE_LOOKUP["CNSHA-INPRT"]
        voyage_engine = VoyageFeasibilityEngine()
        voyage_results = voyage_engine.evaluate_all(feasible_matches, route, SAMPLE_CARGO)
        voyage_feasible = [vr for vr in voyage_results if vr.feasible]
        assert len(voyage_feasible) > 0

        risk_engine = RiskEngine()
        risk_results = risk_engine.assess_all(voyage_feasible, SAMPLE_CARGO)

        assert len(risk_results) == len(voyage_feasible)
        for rr in risk_results:
            assert isinstance(rr, RiskAssessmentResult)
            assert 0.0 <= rr.overall_risk_score <= 100.0
            assert rr.risk_category in RiskCategory
            assert len(rr.factor_scores) == 10
            assert len(rr.reasons) > 0
            assert len(rr.assumptions) > 0
            assert rr.route_id == route.route_id
            assert rr.cargo_id == SAMPLE_CARGO.cargo_id
