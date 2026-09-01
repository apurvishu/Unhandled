"""
Explainability Engine (Phase 12).

Every ``FinalRecommendation`` (Phase 10) must be able to answer:
    - Why this vessel?
    - Why this route?
    - Why this action?
    - Why not the alternatives?

This module answers all four **strictly from data already present** on
the ``FinalRecommendation`` object (``ranked_vessels_on_selected_route``
and ``alternatives``) — it never recomputes a metric independently and
never invents a fact. Because every number quoted here is read
directly off the result it is explaining, the explanation cannot
contradict the result by construction.

No models.py exists for this phase by design (see project structure) —
``ExplanationReport`` is a plain stdlib dataclass, not a new domain
model, since explainability produces derived text, not new data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from optimization_engine.optimization.models import FinalRecommendation


@dataclass
class ExplanationReport:
    """Structured explanation for one FinalRecommendation, all four angles."""

    why_this_vessel: list[str] = field(default_factory=list)
    why_this_route: list[str] = field(default_factory=list)
    why_this_action: list[str] = field(default_factory=list)
    why_not_alternatives: list[str] = field(default_factory=list)
    summary: str = ""

    def as_list(self) -> list[str]:
        """Flatten the report into one ordered list of lines, summary first."""
        lines = [self.summary] if self.summary else []
        lines.extend(self.why_this_vessel)
        lines.extend(self.why_this_route)
        lines.extend(self.why_this_action)
        lines.extend(self.why_not_alternatives)
        return lines


class ExplainabilityEngine:
    """Builds a four-part explanation for a FinalRecommendation.

    Usage::

        explainability_engine = ExplainabilityEngine()
        report = explainability_engine.explain(recommendation)
        print(report.summary)
    """

    def explain(self, recommendation: FinalRecommendation) -> ExplanationReport:
        """Build a complete explanation from an already-computed recommendation.

        Args:
            recommendation: A ``FinalRecommendation`` produced by
                ``FinalRecommendationEngine.recommend()``.

        Returns:
            An ``ExplanationReport``. If the recommendation is
            infeasible, all four sections note that plainly instead of
            fabricating a justification.
        """
        if not recommendation.feasible:
            return ExplanationReport(
                summary=(
                    "No recommendation could be made: no feasible vessel/route "
                    "combination existed for this cargo."
                ),
                why_this_vessel=["No vessel was selected because none were feasible."],
                why_this_route=["No route was selected because no vessel was feasible on it."],
                why_this_action=list(recommendation.explanation),
                why_not_alternatives=[],
            )

        selected_ranked = next(
            (
                rv
                for rv in recommendation.ranked_vessels_on_selected_route
                if rv.vessel_id == recommendation.selected_vessel_id
            ),
            None,
        )
        winner_alt = self._find_winner_alternative(recommendation)

        why_vessel = self._why_this_vessel(recommendation, selected_ranked)
        why_route = self._why_this_route(recommendation)
        why_action = self._why_this_action(recommendation, winner_alt)
        why_not = self._why_not_alternatives(recommendation, winner_alt)

        summary = self._build_summary(recommendation, selected_ranked)

        return ExplanationReport(
            why_this_vessel=why_vessel,
            why_this_route=why_route,
            why_this_action=why_action,
            why_not_alternatives=why_not,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Why this vessel?
    # ------------------------------------------------------------------

    @staticmethod
    def _why_this_vessel(recommendation: FinalRecommendation, selected_ranked) -> list[str]:
        lines = []
        if selected_ranked is None or selected_ranked.raw_metrics is None:
            return [f"{recommendation.selected_vessel_name} was selected (detailed ranking data unavailable)."]

        m = selected_ranked.raw_metrics
        lines.append(
            f"{recommendation.selected_vessel_name} satisfies all Phase 1/2 hard constraints "
            f"and arrives with a {m.deadline_buffer_days:+.2f}-day deadline buffer."
        )

        feasible_others = [
            rv
            for rv in recommendation.ranked_vessels_on_selected_route
            if rv.feasible and rv.vessel_id != selected_ranked.vessel_id and rv.raw_metrics is not None
        ]
        if feasible_others:
            next_best = min(feasible_others, key=lambda rv: rv.rank if rv.rank is not None else float("inf"))
            if next_best.raw_metrics.total_cost > 0:
                cost_diff_pct = (
                    (next_best.raw_metrics.total_cost - m.total_cost) / next_best.raw_metrics.total_cost * 100
                )
                direction = "lower" if cost_diff_pct > 0 else "higher"
                lines.append(
                    f"Its expected voyage cost is {abs(cost_diff_pct):.1f}% {direction} than the "
                    f"next feasible candidate ({next_best.vessel_name})."
                )
            if m.overall_risk_score != next_best.raw_metrics.overall_risk_score:
                comparison = "lower" if m.overall_risk_score < next_best.raw_metrics.overall_risk_score else "higher"
                lines.append(
                    f"Its risk score ({m.overall_risk_score:.1f}/100) is {comparison} than that "
                    f"candidate's ({next_best.raw_metrics.overall_risk_score:.1f}/100)."
                )
        else:
            lines.append("It was the only feasible vessel evaluated on the selected route.")

        return lines

    # ------------------------------------------------------------------
    # Why this route?
    # ------------------------------------------------------------------

    @staticmethod
    def _why_this_route(recommendation: FinalRecommendation) -> list[str]:
        if recommendation.selected_route is None:
            return []
        route_id = recommendation.selected_route.route_id
        other_route_alts = [
            a for a in recommendation.alternatives if a.route is not None and a.route.route_id != route_id
        ]
        if not other_route_alts:
            return [f"Route '{route_id}' was the only route evaluated."]

        best_other = min(other_route_alts, key=lambda a: a.adjusted_cost)
        return [
            f"Route '{route_id}' was chosen over {len(other_route_alts)} alternative route "
            f"option(s); the closest alternative ('{best_other.route.route_id}') had an adjusted "
            f"cost of {best_other.adjusted_cost:,.2f}."
        ]

    # ------------------------------------------------------------------
    # Why this action?
    # ------------------------------------------------------------------

    @staticmethod
    def _why_this_action(recommendation: FinalRecommendation, winner_alt) -> list[str]:
        n = len(recommendation.alternatives)
        line = (
            f"Action '{recommendation.recommended_action.value}' was recommended because it had "
            f"the lowest adjusted cost among {n} alternative(s) considered"
        )
        if winner_alt is not None:
            line += f" ({winner_alt.adjusted_cost:,.2f})."
        else:
            line += "."
        lines = [line]
        if recommendation.expected_savings is not None:
            if abs(recommendation.expected_savings) < 1e-9:
                lines.append("It is tied on raw cost with the next-best alternative.")
            else:
                direction = "cheaper" if recommendation.expected_savings >= 0 else "more expensive"
                lines.append(
                    f"It is {abs(recommendation.expected_savings):,.2f} {direction} (raw cost) than "
                    "the next-best alternative."
                )
        return lines

    # ------------------------------------------------------------------
    # Why not the alternatives?
    # ------------------------------------------------------------------

    @staticmethod
    def _why_not_alternatives(recommendation: FinalRecommendation, winner_alt) -> list[str]:
        lines = []
        for alt in recommendation.alternatives:
            if alt is winner_alt:
                continue
            if not alt.feasible_alternative:
                lines.append(f"Not selected: {alt.action.value} ({alt.vessel_name}) — {alt.notes}")
                continue
            delta = alt.adjusted_cost - (winner_alt.adjusted_cost if winner_alt is not None else 0.0)
            if abs(delta) < 1e-9:
                lines.append(
                    f"Not selected: {alt.action.value} ({alt.vessel_name}"
                    + (f" via '{alt.route.route_id}'" if alt.route else "")
                    + f") — tied with the selected option on adjusted cost "
                    f"({alt.adjusted_cost:,.2f}); the selected option was chosen by "
                    "deterministic tie-break."
                )
                continue
            lines.append(
                f"Not selected: {alt.action.value} ({alt.vessel_name}"
                + (f" via '{alt.route.route_id}'" if alt.route else "")
                + f") — adjusted cost {alt.adjusted_cost:,.2f} is {delta:,.2f} higher than the "
                "selected option."
            )
        return lines

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_winner_alternative(recommendation: FinalRecommendation):
        for alt in recommendation.alternatives:
            same_vessel = alt.vessel_id == recommendation.selected_vessel_id
            same_route = (
                (alt.route is None and recommendation.selected_route is None)
                or (
                    alt.route is not None
                    and recommendation.selected_route is not None
                    and alt.route.route_id == recommendation.selected_route.route_id
                )
            )
            same_action = alt.action == recommendation.recommended_action
            if same_vessel and same_route and same_action:
                return alt
        return None

    @staticmethod
    def _build_summary(recommendation: FinalRecommendation, selected_ranked) -> str:
        if selected_ranked is None or selected_ranked.raw_metrics is None:
            return (
                f"{recommendation.selected_vessel_name} is recommended "
                f"({recommendation.recommended_action.value})."
            )
        m = selected_ranked.raw_metrics
        parts = [
            f"{recommendation.selected_vessel_name} is recommended ({recommendation.recommended_action.value})",
            "because it is feasible",
            f"arrives {m.deadline_buffer_days:.1f} days before the deadline",
        ]
        feasible_others = [
            rv
            for rv in recommendation.ranked_vessels_on_selected_route
            if rv.feasible and rv.vessel_id != selected_ranked.vessel_id and rv.raw_metrics is not None
        ]
        if feasible_others:
            next_best = min(feasible_others, key=lambda rv: rv.rank if rv.rank is not None else float("inf"))
            if next_best.raw_metrics.total_cost > 0:
                cost_diff_pct = (
                    (next_best.raw_metrics.total_cost - m.total_cost) / next_best.raw_metrics.total_cost * 100
                )
                parts.append(
                    f"has {abs(cost_diff_pct):.1f}% {'lower' if cost_diff_pct > 0 else 'higher'} "
                    "expected voyage cost than the next feasible candidate"
                )
            if m.overall_risk_score < next_best.raw_metrics.overall_risk_score:
                parts.append("has a lower risk score")
        return ", ".join(parts) + "."
