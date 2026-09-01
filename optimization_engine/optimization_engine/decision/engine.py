"""
Charter Optimization / Decision Engine (Phase 6).

Turns ranked feasible vessels (Phase 5), optionally across multiple
candidate routes, into an actual charter decision: BOOK_NOW, WAIT,
SELECT_ALTERNATIVE_VESSEL, or SELECT_ALTERNATIVE_ROUTE.

Architecture — "compare, don't cascade":
    Every relevant alternative is built as a ``DecisionAlternative``
    with one commensurable comparison metric (``adjusted_cost``), and
    the engine picks the best one. It does NOT use a priority
    if/elif cascade that stops at the first plausible action — a
    vessel switch being available does not mean WAIT goes unevaluated,
    and vice versa. Every alternative considered is returned in
    ``DecisionResult.alternatives`` for full transparency.

    Alternatives built:
        1. BOOK_NOW with each feasible, risk-acceptable vessel on the
           current route.
        2. WAIT (current route's best vessel, booked later) — only if
           a ``FreightForecastInput`` is supplied. Never fabricated.
        3. BOOK_NOW with the best vessel on each alternative route, if
           ``alternative_routes`` (Phase 8's ``RouteCandidate`` list)
           is supplied.

    The winner is the lowest ``adjusted_cost`` among alternatives that
    clear their feasibility/policy gates (deadline buffer, confidence).
    The action label reflects what actually changed relative to
    Phase 5's own top pick: same vessel/route now -> BOOK_NOW; a
    different vessel on the same route -> SELECT_ALTERNATIVE_VESSEL; a
    different route -> SELECT_ALTERNATIVE_ROUTE; waiting -> WAIT.

No ML lives here. ``FreightForecastInput`` is the only ML-shaped
input, always optional and externally supplied.
"""

from __future__ import annotations

from typing import Optional

from optimization_engine.decision.calculations import (
    calculate_adjusted_cost,
    calculate_expected_waiting_cost,
    calculate_net_expected_benefit,
    calculate_predicted_savings_per_mt,
    clamp,
)
from optimization_engine.decision.models import (
    DecisionAction,
    DecisionAlternative,
    DecisionInput,
    DecisionResult,
    WaitVsBookComparison,
)
from optimization_engine.domain.models import Cargo, Route
from optimization_engine.multiroute.models import RouteCandidate
from optimization_engine.ranking.engine import RankingEngine
from optimization_engine.ranking.models import RankedVessel
from optimization_engine.risk.calculations import calculate_predicted_delay_risk_fallback, classify_risk_category

_BASELINE_ASSUMPTIONS: list[str] = [
    "This engine never fabricates an ML freight forecast: FreightForecastInput must be "
    "supplied externally (mock now, Member 1's ML model later). Without it, WAIT is "
    "never constructed as an alternative.",
    "adjusted_cost is a comparison metric only (total_cost plus a monetized risk term "
    "when risk_cost_per_point > 0); expected_total_cost always remains the real, raw "
    "dollar figure and is never replaced by the adjusted value.",
    "Waiting is assumed to re-book the same vessel later; the model does not track "
    "whether that specific vessel remains available at the forecast horizon.",
    "This module performs no machine learning and uses no mathematical solver; every "
    "alternative is compared via one transparent, deterministic formula.",
]


class DecisionEngine:
    """Compares every relevant charter alternative and recommends the best one.

    Usage::

        decision_engine = DecisionEngine()
        decision = decision_engine.decide(ranked_vessels, cargo)

        # With an external freight forecast and alternative routes
        decision = decision_engine.decide(
            ranked_vessels, cargo,
            current_route=route,
            decision_input=DecisionInput(freight_forecast=forecast),
            alternative_routes=[route_candidate_b, route_candidate_c],
        )
    """

    def decide(
        self,
        ranked_vessels: list[RankedVessel],
        cargo: Cargo,
        *,
        current_route: Optional[Route] = None,
        decision_input: Optional[DecisionInput] = None,
        alternative_routes: Optional[list[RouteCandidate]] = None,
    ) -> DecisionResult:
        """Recommend a charter action by comparing every relevant alternative.

        Args:
            ranked_vessels: Full Phase 5 output for the current route
                (feasible and infeasible mixed together).
            cargo: The cargo requirement being evaluated.
            current_route: Typed route object ``ranked_vessels``
                corresponds to. Used only to label alternatives; pass
                it whenever known.
            decision_input: Configurable policy thresholds and
                optional freight forecast. Defaults to ``DecisionInput()``.
            alternative_routes: Optional Phase 8 output — one
                ``RouteCandidate`` per alternative route. If omitted,
                SELECT_ALTERNATIVE_ROUTE never fires.

        Returns:
            A fully explained ``DecisionResult`` with every alternative
            considered listed in ``.alternatives``.
        """
        decision_input = decision_input if decision_input is not None else DecisionInput()

        feasible = RankingEngine.feasible(ranked_vessels)
        if not feasible:
            return self._no_feasible_option()

        top_ranked_vessel_id = feasible[0].vessel_id

        alternatives: list[DecisionAlternative] = []
        alternatives.extend(self._book_now_alternatives(feasible, current_route, decision_input))

        wait_comparison: Optional[WaitVsBookComparison] = None
        if decision_input.freight_forecast is not None:
            wait_alt, wait_comparison = self._wait_alternative(
                feasible, cargo, current_route, decision_input
            )
            if wait_alt is not None:
                alternatives.append(wait_alt)

        if alternative_routes:
            alternatives.extend(self._route_alternatives(alternative_routes, decision_input))

        return self._choose_best(
            alternatives, top_ranked_vessel_id, current_route, decision_input, wait_comparison, len(feasible)
        )

    # ------------------------------------------------------------------
    # No feasible option
    # ------------------------------------------------------------------

    @staticmethod
    def _no_feasible_option() -> DecisionResult:
        return DecisionResult(
            recommended_action=DecisionAction.NO_FEASIBLE_OPTION,
            reasons=[
                "No feasible vessel meets the cargo's requirements and deadline; "
                "no charter action can be recommended."
            ],
            assumptions=list(_BASELINE_ASSUMPTIONS),
        )

    # ------------------------------------------------------------------
    # Alternative builders
    # ------------------------------------------------------------------

    @staticmethod
    def _book_now_alternatives(
        feasible: list[RankedVessel],
        current_route: Optional[Route],
        decision_input: DecisionInput,
    ) -> list[DecisionAlternative]:
        """Build one BOOK_NOW alternative per feasible, risk-acceptable vessel.

        If NO feasible vessel meets the risk threshold, the single
        least-risky feasible vessel is used as a fallback alternative
        so the engine always has at least one real option to compare —
        flagged clearly in its notes.
        """
        threshold = decision_input.max_acceptable_risk_score
        risk_ok = [rv for rv in feasible if rv.raw_metrics.overall_risk_score <= threshold]
        pool = risk_ok if risk_ok else [min(feasible, key=lambda rv: rv.raw_metrics.overall_risk_score)]

        alternatives = []
        for rv in pool:
            m = rv.raw_metrics
            adjusted = calculate_adjusted_cost(
                m.total_cost, m.overall_risk_score, decision_input.risk_cost_per_point
            )
            within_threshold = rv in risk_ok
            alternatives.append(
                DecisionAlternative(
                    action=DecisionAction.BOOK_NOW,
                    vessel_id=rv.vessel_id,
                    vessel_name=rv.vessel_name,
                    route=current_route,
                    expected_total_cost=m.total_cost,
                    adjusted_cost=adjusted,
                    risk_score=m.overall_risk_score,
                    deadline_buffer_days=m.deadline_buffer_days,
                    feasible_alternative=True,
                    notes=(
                        f"Book {rv.vessel_name} now (rank #{rv.rank} of {len(feasible)}); "
                        f"risk {m.overall_risk_score:.1f} "
                        + ("within" if within_threshold else "EXCEEDS")
                        + f" threshold {threshold:.1f}"
                        + ("" if within_threshold else " (used as fallback — no vessel met it)")
                        + "."
                    ),
                )
            )
        return alternatives

    @staticmethod
    def _wait_alternative(
        feasible: list[RankedVessel],
        cargo: Cargo,
        current_route: Optional[Route],
        decision_input: DecisionInput,
    ) -> tuple[Optional[DecisionAlternative], Optional[WaitVsBookComparison]]:
        """Build the WAIT alternative: book the same (best) vessel later at the forecast rate."""
        threshold = decision_input.max_acceptable_risk_score
        risk_ok = [rv for rv in feasible if rv.raw_metrics.overall_risk_score <= threshold]
        pool = risk_ok if risk_ok else feasible
        best = min(
            pool,
            key=lambda rv: calculate_adjusted_cost(
                rv.raw_metrics.total_cost,
                rv.raw_metrics.overall_risk_score,
                decision_input.risk_cost_per_point,
            ),
        )
        m = best.raw_metrics
        forecast = decision_input.freight_forecast

        wait_days = forecast.forecast_horizon_days
        buffer_after_wait = m.deadline_buffer_days - wait_days
        expected_waiting_cost = calculate_expected_waiting_cost(
            decision_input.waiting_cost_per_day, decision_input.congestion_cost_per_day, wait_days
        )
        predicted_total_cost = forecast.predicted_freight_rate_per_mt * cargo.quantity_mt
        wait_total_cost = predicted_total_cost + expected_waiting_cost

        # Risk impact of waiting: re-derive the deadline-buffer-driven delay
        # component with the smaller post-wait buffer, and apply the delta
        # to the vessel's already-computed overall risk score. This reuses
        # Phase 4's own deterministic formula rather than duplicating it.
        original_delay_component = calculate_predicted_delay_risk_fallback(m.deadline_buffer_days)
        new_delay_component = calculate_predicted_delay_risk_fallback(buffer_after_wait)
        risk_after_wait = clamp(m.overall_risk_score + (new_delay_component - original_delay_component))

        wait_adjusted_cost = calculate_adjusted_cost(
            wait_total_cost, risk_after_wait, decision_input.risk_cost_per_point
        )

        buffer_ok = buffer_after_wait >= decision_input.min_acceptable_deadline_buffer_days
        confidence_ok = (
            forecast.confidence is None or forecast.confidence >= decision_input.min_confidence_threshold
        )
        feasible_alt = buffer_ok and confidence_ok

        predicted_savings_per_mt = calculate_predicted_savings_per_mt(
            m.cost_per_mt, forecast.predicted_freight_rate_per_mt
        )
        comparison = WaitVsBookComparison(
            current_cost_per_mt=m.cost_per_mt,
            predicted_cost_per_mt=forecast.predicted_freight_rate_per_mt,
            predicted_savings_per_mt=predicted_savings_per_mt,
            predicted_total_savings=predicted_savings_per_mt * cargo.quantity_mt,
            expected_wait_days=wait_days,
            expected_waiting_cost=expected_waiting_cost,
            net_expected_benefit_of_waiting=calculate_net_expected_benefit(
                m.total_cost, wait_total_cost
            ),
            deadline_buffer_after_wait_days=buffer_after_wait,
            meets_confidence_threshold=confidence_ok if forecast.confidence is not None else None,
        )

        note = f"Wait {wait_days:.1f} days for forecast rate {forecast.predicted_freight_rate_per_mt:.2f}/MT."
        if not buffer_ok:
            note += (
                f" EXCLUDED: post-wait deadline buffer {buffer_after_wait:.2f} days is below "
                f"the required {decision_input.min_acceptable_deadline_buffer_days:.2f}."
            )
        if not confidence_ok:
            note += (
                f" EXCLUDED: forecast confidence {forecast.confidence:.2f} is below the "
                f"required {decision_input.min_confidence_threshold:.2f}."
            )

        alternative = DecisionAlternative(
            action=DecisionAction.WAIT,
            vessel_id=best.vessel_id,
            vessel_name=best.vessel_name,
            route=current_route,
            expected_total_cost=wait_total_cost,
            adjusted_cost=wait_adjusted_cost,
            risk_score=risk_after_wait,
            deadline_buffer_days=buffer_after_wait,
            feasible_alternative=feasible_alt,
            notes=note,
        )
        return alternative, comparison

    @staticmethod
    def _route_alternatives(
        alternative_routes: list[RouteCandidate], decision_input: DecisionInput
    ) -> list[DecisionAlternative]:
        alternatives = []
        for candidate in alternative_routes:
            route_feasible = RankingEngine.feasible(candidate.ranked_vessels)
            if not route_feasible:
                continue
            threshold = decision_input.max_acceptable_risk_score
            risk_ok = [rv for rv in route_feasible if rv.raw_metrics.overall_risk_score <= threshold]
            pool = risk_ok if risk_ok else route_feasible
            best = min(
                pool,
                key=lambda rv: calculate_adjusted_cost(
                    rv.raw_metrics.total_cost,
                    rv.raw_metrics.overall_risk_score,
                    decision_input.risk_cost_per_point,
                ),
            )
            m = best.raw_metrics
            adjusted = calculate_adjusted_cost(
                m.total_cost, m.overall_risk_score, decision_input.risk_cost_per_point
            )
            alternatives.append(
                DecisionAlternative(
                    action=DecisionAction.SELECT_ALTERNATIVE_ROUTE,
                    vessel_id=best.vessel_id,
                    vessel_name=best.vessel_name,
                    route=candidate.route,
                    expected_total_cost=m.total_cost,
                    adjusted_cost=adjusted,
                    risk_score=m.overall_risk_score,
                    deadline_buffer_days=m.deadline_buffer_days,
                    feasible_alternative=True,
                    notes=(
                        f"Best option via route '{candidate.route.route_id}': "
                        f"{best.vessel_name}, cost {m.total_cost:,.2f}, risk "
                        f"{m.overall_risk_score:.1f}."
                    ),
                )
            )
        return alternatives

    # ------------------------------------------------------------------
    # Final selection among all alternatives
    # ------------------------------------------------------------------

    @staticmethod
    def _choose_best(
        alternatives: list[DecisionAlternative],
        top_ranked_vessel_id: str,
        current_route: Optional[Route],
        decision_input: DecisionInput,
        wait_comparison: Optional[WaitVsBookComparison],
        feasible_count: int,
    ) -> DecisionResult:
        viable = [a for a in alternatives if a.feasible_alternative]
        if not viable:
            viable = [a for a in alternatives if a.action == DecisionAction.BOOK_NOW]

        best = min(viable, key=lambda a: a.adjusted_cost)

        # Guard against churn: only switch away from the primary BOOK_NOW
        # option (Phase 5's own top pick, on the current route) if the
        # improvement clears the configured minimum margin.
        primary = next(
            (
                a
                for a in alternatives
                if a.action == DecisionAction.BOOK_NOW and a.vessel_id == top_ranked_vessel_id
            ),
            None,
        )
        if primary is not None and best is not primary:
            if primary.adjusted_cost <= 0:
                improvement_pct = 100.0 if best.adjusted_cost < primary.adjusted_cost else 0.0
            else:
                improvement_pct = (primary.adjusted_cost - best.adjusted_cost) / primary.adjusted_cost * 100.0
            if improvement_pct < decision_input.min_switch_improvement_pct:
                best = primary

        # Relabel BOOK_NOW-on-a-different-vessel as SELECT_ALTERNATIVE_VESSEL,
        # so the action always reflects what actually changed vs Phase 5's pick.
        final_action = best.action
        if (
            best.action == DecisionAction.BOOK_NOW
            and best.vessel_id != top_ranked_vessel_id
        ):
            final_action = DecisionAction.SELECT_ALTERNATIVE_VESSEL

        # Expected savings: raw-dollar difference vs the next-best alternative.
        others = sorted(
            (a for a in alternatives if a is not best), key=lambda a: a.adjusted_cost
        )
        expected_savings = (
            others[0].expected_total_cost - best.expected_total_cost if others else None
        )

        reasons = DecisionEngine._build_reasons(
            best, final_action, alternatives, top_ranked_vessel_id, current_route, feasible_count
        )

        return DecisionResult(
            recommended_action=final_action,
            selected_vessel_id=best.vessel_id,
            selected_vessel_name=best.vessel_name,
            selected_route=best.route,
            expected_total_cost=best.expected_total_cost,
            cost_per_mt=None,
            adjusted_cost=best.adjusted_cost,
            wait_vs_book_comparison=wait_comparison if final_action == DecisionAction.WAIT else None,
            expected_savings=expected_savings,
            deadline_impact_days=best.deadline_buffer_days,
            risk_score=best.risk_score,
            risk_category=classify_risk_category(best.risk_score) if best.risk_score is not None else None,
            alternatives=alternatives,
            reasons=reasons,
            assumptions=list(_BASELINE_ASSUMPTIONS),
        )

    @staticmethod
    def _build_reasons(
        best: DecisionAlternative,
        final_action,
        alternatives: list[DecisionAlternative],
        top_ranked_vessel_id: str,
        current_route: Optional[Route],
        feasible_count: int,
    ) -> list[str]:
        reasons = [
            f"Compared {len(alternatives)} alternative(s): "
            + "; ".join(
                f"{a.action.value} {a.vessel_name or ''}"
                f"{(' via ' + a.route.route_id) if a.route else ''} "
                f"(adjusted cost {a.adjusted_cost:,.2f})"
                for a in alternatives
            )
            + "."
        ]
        reasons.append(
            f"Recommended: {final_action.value} — {best.vessel_name} "
            + (f"via route '{best.route.route_id}' " if best.route else "")
            + f"at adjusted cost {best.adjusted_cost:,.2f} (raw cost {best.expected_total_cost:,.2f})."
        )
        if final_action == DecisionAction.SELECT_ALTERNATIVE_VESSEL:
            reasons.append(
                f"This differs from Phase 5's top-ranked vessel ('{top_ranked_vessel_id}') "
                "because it has a lower adjusted cost among risk-acceptable options."
            )
        if final_action == DecisionAction.SELECT_ALTERNATIVE_ROUTE:
            reasons.append(
                f"This differs from the current route "
                f"('{current_route.route_id if current_route else 'unspecified'}') "
                "because the alternative route's best vessel has a lower adjusted cost."
            )
        excluded = [a for a in alternatives if not a.feasible_alternative]
        for a in excluded:
            reasons.append(f"Excluded from consideration: {a.notes}")
        return reasons
