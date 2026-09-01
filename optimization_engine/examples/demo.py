"""
Demonstration script for the Maritime Optimization Engine.

Runs the COMPLETE pipeline (Phases 1-12) against the mock vessel
dataset for the canonical scenario:

    Cargo:    75,000 MT iron ore
    Origin:   Shanghai
    Dest:     Paradip
    Deadline: 15 October 2026

    Matching -> Rejected/Feasible -> ETA -> Cost -> Risk -> Ranking
    -> Decision alternatives -> Final recommendation -> Explanation

*** ALL DATA IN THIS DEMO IS MOCK/DEMO DATA. ***
Vessel specs, port limits, route distances, cost rates, risk factors,
and the freight forecast are all fixtures for development and
demonstration only — none of it is live maritime, AIS, weather, or
market data. See README.md for exactly which fields are mock and
which are real formulas applied to that mock data.

Usage:
    python -m examples.demo
"""

from __future__ import annotations

from optimization_engine.data.mock.fixtures import (
    MOCK_FREIGHT_FORECAST,
    MOCK_VESSELS,
    PARADIP,
    ROUTE_LOOKUP,
    SAMPLE_CARGO,
    SAMPLE_COST_INPUT,
    SHANGHAI,
)
from optimization_engine.decision.models import DecisionInput
from optimization_engine.explainability.engine import ExplainabilityEngine
from optimization_engine.matching.engine import MatchingEngine
from optimization_engine.optimization.engine import FinalRecommendationEngine
from optimization_engine.voyage.engine import VoyageFeasibilityEngine

_DIVIDER = "=" * 78
_THIN_DIVIDER = "-" * 78


def _print_header() -> None:
    print()
    print(_DIVIDER)
    print("  MARITIME OPTIMIZATION ENGINE — FULL PIPELINE DEMO")
    print("  Phases 1-12: Matching -> Feasibility -> Economics -> Risk -> Ranking")
    print("               -> Decision -> Final Recommendation -> Explanation")
    print(_DIVIDER)
    print()
    print("  *** ALL DATA BELOW IS MOCK/DEMO DATA — NOT LIVE MARITIME DATA ***")
    print()
    print(f"  Cargo:        {SAMPLE_CARGO.quantity_mt:,.0f} MT {SAMPLE_CARGO.cargo_type}")
    print(f"  Origin:       {SHANGHAI.port_name} ({SHANGHAI.port_id})")
    print(f"  Destination:  {PARADIP.port_name} ({PARADIP.port_id})")
    print(f"  Deadline:     {SAMPLE_CARGO.required_arrival_date.isoformat()}")
    print(f"  Candidates:   {len(MOCK_VESSELS)} vessels (mock fleet)")
    print()
    print(_THIN_DIVIDER)


def _section(title: str) -> None:
    print()
    print(f"  {title}")
    print(_THIN_DIVIDER)


def main() -> None:
    _print_header()

    route = ROUTE_LOOKUP["CNSHA-INPRT"]

    # ── Phase 1: Vessel Matching (shown explicitly for the rejected/feasible view) ──
    matching_engine = MatchingEngine()
    match_results = matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
    feasible_matches = matching_engine.feasible(match_results)
    rejected_matches = matching_engine.rejected(match_results)

    _section(f"❌  PHASE 1 REJECTED  ({len(rejected_matches)})")
    if not rejected_matches:
        print("  (none)")
    else:
        for r in rejected_matches:
            print(f"\n  {r.vessel.vessel_name}")
            for reason in r.rejection_reasons:
                print(f"    -> {reason}")

    # ── Phase 2: Voyage Feasibility / ETA (shown explicitly) ──
    voyage_engine = VoyageFeasibilityEngine()
    voyage_results = voyage_engine.evaluate_all(feasible_matches, route, SAMPLE_CARGO)
    voyage_feasible = [vr for vr in voyage_results if vr.feasible]
    voyage_infeasible = [vr for vr in voyage_results if not vr.feasible]

    _section(f"✅  PHASE 1+2 FEASIBLE  ({len(voyage_feasible)})")
    for vr in voyage_feasible:
        v = vr.vessel
        print(f"\n  {v.vessel_name}")
        print(f"    Speed:               {v.speed_knots} kn")
        print(f"    Estimated arrival:   {vr.estimated_arrival.strftime('%d %B %Y at %H:%M')}")
        print(f"    Deadline buffer:     {vr.deadline_buffer_days:+.2f} days")

    if voyage_infeasible:
        _section(f"⚠️   DEADLINE MISSED  ({len(voyage_infeasible)})")
        for vr in voyage_infeasible:
            print(f"\n  {vr.vessel.vessel_name}: buffer {vr.deadline_buffer_days:+.2f} days")

    # ── Phases 3-10: run the whole thing through the FinalRecommendationEngine ──
    # (These are the same Phase 3/4/5 engines shown above, just orchestrated —
    # see optimization_engine/optimization/engine.py for the exact call sequence.)
    final_engine = FinalRecommendationEngine()
    recommendation = final_engine.recommend(
        SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, route, SAMPLE_COST_INPUT,
        decision_input=DecisionInput(freight_forecast=MOCK_FREIGHT_FORECAST),
    )

    # ── Phase 3/4/5 detail: cost, risk, and ranking for every feasible vessel ──
    from optimization_engine.ranking.engine import RankingEngine

    _section(f"💰📊🏆  COST / RISK / RANKING  ({len(recommendation.ranked_vessels_on_selected_route)})")
    print(f"  {'Rank':<5}{'Vessel':<22}{'Cost (USD)':>14}{'Risk':>8}{'Buffer (d)':>12}{'Score':>8}")
    for rv in RankingEngine.feasible(recommendation.ranked_vessels_on_selected_route):
        m = rv.raw_metrics
        print(
            f"  {rv.rank:<5}{rv.vessel_name:<22}{m.total_cost:>14,.0f}"
            f"{m.overall_risk_score:>8.1f}{m.deadline_buffer_days:>12.1f}{rv.overall_score:>8.1f}"
        )

    # ── Phase 6: Decision alternatives ──
    _section(f"🧭  DECISION ALTERNATIVES  ({len(recommendation.alternatives)} considered)")
    print(f"  Freight forecast supplied (mock): {MOCK_FREIGHT_FORECAST.predicted_freight_rate_per_mt}/MT "
          f"in {MOCK_FREIGHT_FORECAST.forecast_horizon_days:.0f} days "
          f"(confidence {MOCK_FREIGHT_FORECAST.confidence:.2f}, source='{MOCK_FREIGHT_FORECAST.source}')")
    print()
    for alt in recommendation.alternatives:
        marker = "  " if alt.feasible_alternative else "✗ "
        route_label = f" via {alt.route.route_id}" if alt.route else ""
        print(f"  {marker}{alt.action.value:<26}{alt.vessel_name or '-':<20}"
              f"adjusted={alt.adjusted_cost:>14,.2f}{route_label}")
        if not alt.feasible_alternative:
            print(f"      excluded: {alt.notes}")

    # ── Phase 10: Final recommendation ──
    _section("🎯  FINAL RECOMMENDATION")
    print(f"  Action:            {recommendation.recommended_action.value}")
    print(f"  Vessel:            {recommendation.selected_vessel_name}")
    print(f"  Route:             {recommendation.selected_route.route_id}")
    print(f"  ETA:               {recommendation.estimated_arrival.strftime('%d %B %Y at %H:%M')}")
    print(f"  Deadline buffer:   {recommendation.deadline_buffer_days:+.2f} days")
    print(f"  Total cost:        {recommendation.expected_total_cost:,.2f} USD")
    print(f"  Cost per MT:       {recommendation.cost_per_mt:,.2f} USD/MT")
    print(f"  Risk score:        {recommendation.risk_score:.1f}/100 ({recommendation.risk_category.value})")
    if recommendation.emissions:
        print(f"  Emissions:         {recommendation.emissions.co2_emissions_mt:,.2f} MT CO2 "
              f"({recommendation.emissions.co2_per_tonne_kg:.2f} kg/MT cargo) [mock emission factor]")
    if recommendation.expected_savings is not None:
        print(f"  Expected savings:  {recommendation.expected_savings:,.2f} USD vs. next-best alternative")

    # ── Phase 12: Explanation ──
    explanation = ExplainabilityEngine().explain(recommendation)
    _section("💬  EXPLANATION")
    print(f"\n  {explanation.summary}\n")
    print("  Why this vessel?")
    for line in explanation.why_this_vessel:
        print(f"    -> {line}")
    print("\n  Why this route?")
    for line in explanation.why_this_route:
        print(f"    -> {line}")
    print("\n  Why this action?")
    for line in explanation.why_this_action:
        print(f"    -> {line}")
    print("\n  Why not the alternatives?")
    for line in explanation.why_not_alternatives:
        print(f"    -> {line}")

    # ── Summary ──
    print()
    print(_DIVIDER)
    print("  Summary:")
    print(f"    Phase 1:  {len(feasible_matches)} compatible / {len(rejected_matches)} rejected")
    print(f"    Phase 2:  {len(voyage_feasible)} voyage feasible / {len(voyage_infeasible)} deadline missed")
    print(f"    Phase 6:  {recommendation.recommended_action.value} recommended "
          f"({len(recommendation.alternatives)} alternatives compared)")
    print(f"    Total:    {len(MOCK_VESSELS)} candidates evaluated")
    print(_DIVIDER)
    print()
    print("  Reminder: every number above comes from mock/demo data.")
    print("  See README.md for the full mock-vs-real breakdown and formulas.")
    print()


if __name__ == "__main__":
    main()
