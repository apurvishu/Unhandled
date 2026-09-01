# Maritime Optimization Engine

**PS-SIH26006** — Development of an Intelligent Freight Forecasting Model for Optimized Vessel Chartering and Bulk Cargo Procurement from Overseas to the East Coast of India.

> **Status:** Phases 1–15 complete. Standalone prototype using mock data.
> No database, no APIs, no ML, no frontend, no OR-Tools (no mathematical
> optimization problem has been defined that would justify one).

This module answers one question end to end:

> *"For a cargo requirement of X metric tonnes from origin A to destination B with deadline D, which vessel/route/action should be selected, at what expected cost, with what risk, and why?"*

---

## What This Component Does

Given a cargo requirement (e.g. 75,000 MT iron ore, Shanghai → Paradip, by 15 Oct 2026), the engine runs a 10-stage deterministic pipeline:

1. **Phase 1 — Vessel Matching:** Hard constraints (capacity, cargo type, availability window, operational status, port dimensional compatibility). Feasible/rejected split, all rejection reasons collected.
2. **Phase 2 — Voyage Feasibility & ETA:** Deterministic sailing-time calculation, deadline buffer, combined feasibility.
3. **Phase 3 — Voyage Economics:** Fully itemized voyage cost breakdown (charter, fuel, port, waiting, insurance, etc.), total cost and cost/MT.
4. **Phase 4 — Risk Assessment:** Ten configurable, weighted risk factors → one 0–100 score with a full breakdown.
5. **Phase 5 — Vessel Ranking:** Six weighted components (cost, risk, deadline buffer, cargo suitability, availability, operational suitability) → one 0–100 ranking score. Infeasible vessels structurally excluded.
6. **Phase 6 — Charter Decision:** Compares *every* relevant alternative (book each risk-acceptable vessel now, wait if a forecast justifies it, book the best vessel on each alternative route) on one commensurable metric, and recommends BOOK_NOW / WAIT / SELECT_ALTERNATIVE_VESSEL / SELECT_ALTERNATIVE_ROUTE.
7. **Phase 7 — What-If Simulation:** Answers "what happens if fuel/freight/deadline/cargo/vessel/route changes?" by reusing Phases 1–4 on a modified copy of the inputs — the originals are never mutated.
8. **Phase 8 — Multi-Route Comparison:** Ranks externally-supplied candidate routes the same way Phase 5 ranks vessels; the cheapest route never automatically wins.
9. **Phase 9 — Emissions (optional):** CO2 from fuel already consumed, per-tonne and per-tonne-km, with a clearly labeled non-regulatory emission factor.
10. **Phase 10 — Final Orchestration:** Combines Phases 1–9 into one `FinalRecommendation`. Deliberately **not** called an "optimization solver" — no OR-Tools, no defined decision variables/objective/constraints exist.

On top of the pipeline:

- **Phase 11 — Integration Contracts:** Typed `Protocol` interfaces for what Members 1/2/4 will eventually supply; zero HTTP/DB/ML framework imports anywhere in the core engine (verified by a static scan in the test suite).
- **Phase 12 — Explainability:** Answers "why this vessel / why this route / why this action / why not the alternatives" strictly from the numbers already in the result — it cannot contradict the result because it never recomputes anything independently.

### Key Distinction

| Phase | Answers | Type |
|---|---|---|
| Phase 1 | Is this vessel *compatible* with the cargo and port? | Static compatibility (hard constraint) |
| Phase 2 | Can this vessel *reach the destination in time*? | Voyage feasibility (hard constraint) |
| Phase 5 | *Which* feasible vessel is better, all things considered? | Ranking (relative scoring) |
| Phase 6 | *What should we actually do* — book, wait, or switch? | Decision (alternative comparison) |
| Phase 10 | Combine all of the above into one recommendation | Orchestration (**not** a solver) |

A vessel must pass **both** Phase 1 and Phase 2 to be considered feasible; ranking and decision-making never override that.

## What This Component Does NOT Do

| Capability | Status |
|---|---|
| Mathematical/solver-based optimization (OR-Tools etc.) | Not introduced — no decision variables/objective/constraints have been defined that would justify it (see Phase 10) |
| ML freight/demand/congestion/delay forecasting | Built by AI/ML team (Member 1) — this engine only defines the typed contracts it expects (Phase 11) |
| AIS vessel tracking, live positions | Built by Geospatial team (Member 4) — `Vessel.current_location` exists but is unused by any engine |
| Real navigational routing | Built by Geospatial team (Member 4) — this engine only ever consumes `Route` objects it's given |
| PostgreSQL / PostGIS / persistence | Built by Backend team (Member 2) |
| FastAPI / HTTP endpoints | Built by Backend team (Member 2) |
| Frontend dashboards | Built by Frontend team (Member 3) |
| Regulatory emissions compliance claims (IMO CII/EEXI etc.) | Explicitly disclaimed — Phase 9's emission factor is a labeled approximation |

---

## Project Structure

```
optimization_engine/
├── __init__.py
├── domain/
│   ├── __init__.py
│   └── models.py              # Cargo, Vessel, Port, Route, MatchResult,
│                               #   VoyageFeasibilityResult (Phase 1-2, stable)
├── rules/
│   ├── __init__.py
│   └── constraints.py         # 7 pure-function hard constraints (Phase 1)
├── matching/
│   ├── __init__.py
│   └── engine.py              # MatchingEngine (Phase 1)
├── voyage/
│   ├── __init__.py
│   ├── sailing.py             # Pure sailing-time calculation functions
│   └── engine.py              # VoyageFeasibilityEngine (Phase 2)
├── economics/
│   ├── __init__.py
│   ├── models.py              # VoyageCostInput, VoyageCostBreakdown
│   ├── calculations.py        # Pure cost-calculation functions
│   └── engine.py              # VoyageEconomicsEngine (Phase 3)
├── risk/
│   ├── __init__.py
│   ├── models.py               # RiskFactorInput, RiskWeights, RiskFactorScore,
│   │                            #   RiskAssessmentResult, RiskCategory
│   ├── calculations.py         # Pure risk-factor calculation functions
│   └── engine.py                # RiskEngine (Phase 4)
├── ranking/
│   ├── __init__.py
│   ├── models.py                # RankingWeights, RankingComponentScore,
│   │                             #   RankingRawMetrics, RankedVessel
│   ├── calculations.py          # Pure ranking-component calculation functions
│   └── engine.py                 # RankingEngine (Phase 5)
├── decision/
│   ├── __init__.py
│   ├── models.py                  # DecisionAction, FreightForecastInput,
│   │                               #   DecisionInput, DecisionAlternative, DecisionResult
│   ├── calculations.py            # Pure decision calculation functions
│   └── engine.py                   # DecisionEngine (Phase 6)
├── simulation/
│   ├── __init__.py
│   ├── models.py                    # ScenarioType, ScenarioChange, ScenarioResult
│   └── engine.py                     # ScenarioSimulator (Phase 7) — reuses Phases 1-4
├── multiroute/
│   ├── __init__.py
│   ├── models.py                      # RouteCandidate, RouteWeights, RankedRoute
│   └── engine.py                       # MultiRouteEngine (Phase 8)
├── emissions/
│   ├── __init__.py
│   ├── models.py                        # EmissionsInput, EmissionsResult
│   ├── calculations.py                  # Pure emissions calculation functions
│   └── engine.py                         # EmissionsEngine (Phase 9)
├── optimization/
│   ├── __init__.py
│   ├── models.py                          # AlternativeRouteInput, FinalRecommendation
│   └── engine.py                           # FinalRecommendationEngine (Phase 10 —
│                                            #   orchestration, NOT a mathematical solver)
├── integration/
│   ├── __init__.py
│   ├── contracts.py                        # 9 typing.Protocol interfaces (Phase 11)
│   └── adapters.py                         # Mock/demo-only adapters, fixtures-backed
├── explainability/
│   ├── __init__.py
│   └── engine.py                           # ExplainabilityEngine (Phase 12) —
│                                            #   ExplanationReport is a plain dataclass
└── data/
    ├── __init__.py
    └── mock/
        ├── __init__.py
        └── fixtures.py        # 21 vessels, 3 ports, 6 routes, sample cargo,
                                #   SAMPLE_COST_INPUT, SAMPLE_RISK_INPUT/WEIGHTS,
                                #   SAMPLE_RANKING_WEIGHTS, MOCK_FREIGHT_FORECAST

tests/
├── __init__.py
├── test_constraints.py            # Phase 1
├── test_matching_engine.py        # Phase 1
├── test_sailing.py                # Phase 2
├── test_voyage_engine.py          # Phase 2
├── test_economics.py              # Phase 3
├── test_risk.py                   # Phase 4
├── test_ranking.py                # Phase 5
├── test_decision.py               # Phase 6
├── test_simulation.py             # Phase 7
├── test_multiroute.py             # Phase 8
├── test_emissions.py              # Phase 9
├── test_optimization.py           # Phase 10
├── test_integration_contracts.py  # Phase 11
├── test_explainability.py         # Phase 12
├── test_robustness.py             # Phase 13 (consolidated edge-case audit)
├── test_end_to_end.py             # Phase 14 (canonical scenario, full pipeline)
└── test_demo.py                   # Phase 15 (demo script actually executed)

examples/
└── demo.py                    # Full-pipeline CLI demo (Phases 1-12)

pyproject.toml
.gitignore
README.md
BRAIN.md               # Compact session-resumption state for AI agents
PROJECT_CONTEXT.md     # Broader project context / handoff document
CLAUDE.md              # Permanent instructions for future agents
```

---

## Phase 1 — Vessel Matching

### Domain Models

| Model | Purpose |
|---|---|
| `Cargo` | What needs to be shipped, where, and by when |
| `Vessel` | Physical specs, operational status, supported cargo types |
| `Port` | Static physical constraints (max draft, LOA, beam) |
| `MatchResult` | Feasibility verdict with all constraint checks and rejection reasons |

Key distinctions:
- **`status`** = operational readiness (can the vessel sail?)
- **`available_from`** = temporal availability (when does the current commitment end?)
- These are independent — both must pass.

### Hard Constraints (7)

| # | Constraint | What it checks |
|---|---|---|
| 1 | **Capacity** | `vessel.cargo_capacity_mt >= cargo.quantity_mt` |
| 2 | **Cargo Compatibility** | `cargo.cargo_type in vessel.cargo_types_supported` |
| 3 | **Availability Window** | `vessel.available_from <= cargo.required_arrival_date` — vessel is available within the planning window. **Not** ETA feasibility. |
| 4 | **Status** | Excludes `UNDER_MAINTENANCE` and `LAID_UP` |
| 5 | **Static Draft Compatibility** | `vessel.draft_m <= port.max_draft_m` — dimensional fit, **not** navigational safety |
| 6 | **Static LOA Compatibility** | `vessel.loa_m <= port.max_loa_m` |
| 7 | **Static Beam Compatibility** | `vessel.beam_m <= port.max_beam_m` |

All constraints run for every vessel (no short-circuit). All rejection reasons are collected.

---

## Phase 2 — Voyage Feasibility & Baseline ETA

### Additional Models

| Model | Purpose |
|---|---|
| `Route` | Origin, destination, distance in nautical miles |
| `VoyageFeasibilityResult` | Full voyage assessment: ETA, deadline check, buffer, combined feasibility |

### Sailing-Time Calculation

```
sailing_hours = distance_nm / speed_knots     (1 knot = 1 nm/hour)
sailing_days  = sailing_hours / 24
```

### Estimated Departure

```
estimated_departure = vessel.available_from at 00:00
```

> **Assumption:** The vessel is ready at the origin port on its `available_from` date. This does not model current AIS position, repositioning, loading time, charter negotiation, berth availability, or port waiting.

### Estimated Arrival

```
estimated_arrival = estimated_departure + timedelta(hours=sailing_hours)
```

Uses `datetime` (not `date`) to preserve sub-day precision.

### Deadline Interpretation

A `required_arrival_date` of 15 October 2026 means:

> The vessel must arrive by the **end of that calendar day** (23:59:59).

This prevents a vessel arriving at noon from being incorrectly classified as late.

### Deadline Buffer

```
deadline_buffer_days = (deadline - estimated_arrival).total_seconds() / 86400
```

| Buffer | Meaning |
|---|---|
| `+8.27` | Arrives 8.27 days early |
| `0.00` | Arrives exactly at deadline |
| `-3.33` | Arrives 3.33 days late |

Uses `total_seconds() / 86400` instead of `.days` to preserve fractional precision.

### Overall Feasibility

```
feasible = phase1_feasible AND deadline_feasible
```

A Phase 1 rejection **cannot** be overridden by a good ETA.

### Mock Route Data

| Route | Distance (nm) |
|---|---|
| Shanghai → Paradip | 3,450 |
| Shanghai → Visakhapatnam | 3,520 |
| Singapore → Paradip | 1,850 |
| Colombo → Paradip | 950 |
| Colombo → Visakhapatnam | 680 |
| Paradip → Shanghai | 3,450 |

> **Important:** These are mock planning distances, not authoritative navigational data. Real distances will come from the Geospatial team's routing engine.

---

## Phase 2 — Limitations & Assumptions

Phase 2 currently **does not model**:

- Weather, ocean currents, or wave conditions
- Port congestion or berth waiting time
- Loading/unloading duration
- Current AIS position or real vessel routing
- Navigable route optimization
- Speed reduction or fuel optimization
- Tidal windows or under-keel clearance
- Real-world timezone handling
- Multiple voyage legs
- ML-based ETA predictions

The `vessel.current_location` field exists but is intentionally unused by the baseline ETA engine. Real vessel-position routing belongs to the Geospatial/AIS component (Member 4).

---

## Phase 3 — Voyage Economics

Given a `VoyageFeasibilityResult` (Phase 2) and a configurable `VoyageCostInput`, `VoyageEconomicsEngine.calculate()` returns a fully itemized `VoyageCostBreakdown`.

### Cost Components

| Component | Formula |
|---|---|
| Charter/freight | `freight_rate_per_mt × cargo_quantity_mt` |
| Fuel | `fuel_consumption_mt_per_day × sailing_days × fuel_price_per_mt` |
| Port (fixed), pilotage, tug | Direct pass-through inputs |
| Berth | `berth_charge_per_day × port_days` |
| Cargo handling | `cargo_handling_rate_per_mt × cargo_quantity_mt` |
| Waiting | `waiting_cost_per_day × expected_waiting_days` |
| Demurrage | `demurrage_rate_per_day × expected_demurrage_days` |
| Storage | `storage_rate_per_day × storage_days` |
| Insurance | `insurance_rate_per_mt × cargo_quantity_mt` |
| Maintenance | `maintenance_cost_per_day × (sailing_days + port_days + waiting_days)` |
| Tax, duty, other | Direct pass-through inputs (default 0) |

`total_cost` is the arithmetic sum of every component above — never a black-box number. `cost_per_mt = total_cost / cargo_quantity_mt`.

> **All rates in `VoyageCostInput` are mock/demo values.** Real rates will come from the Backend team's tariff APIs, ML freight forecasts, and port-authority data.

---

## Phase 4 — Risk Assessment

Given a vessel/cargo (optionally with a route and a Phase 2 deadline buffer), `RiskEngine.assess()` returns a deterministic, explainable `RiskAssessmentResult` with a single 0–100 overall risk score.

### Risk Factors (10, each scored 0–100, higher = riskier)

| Factor | Default weight | Source |
|---|---|---|
| Weather | 0.10 | Mock input (future: Geospatial weather data) |
| Congestion | 0.10 | Mock input (future: ML congestion forecast / AIS density) |
| Vessel age | 0.10 | Derived from `vessel_age_years` via a piecewise-linear formula (≤5 yrs → 10, ≥25 yrs → 90); if age is unknown, a documented default (40) is used |
| Vessel condition/maintenance | 0.15 | Mock input (future: Backend maintenance records) |
| Route hazard/security | 0.10 | Mock input (future: Geospatial routing layer) |
| Port restriction | 0.05 | Mock input (future: Backend port-authority data) |
| Cargo hazard | 0.10 | Derived from `Cargo.hazardous` (65 if hazardous, 10 otherwise) unless explicitly overridden |
| Documentation/compliance | 0.10 | Mock input (future: Backend compliance records) |
| Predicted delay | 0.15 | **External ML input only** (Member 1). If not supplied, a deterministic deadline-buffer proxy is used instead and flagged as an estimate — never fabricated as a prediction |
| Historical incidents | 0.05 | Mock input (future: Backend incident records) |

### Weighting

```
normalized_weight_i = weight_i / sum(all weights)
weighted_contribution_i = raw_score_i × normalized_weight_i
overall_risk_score = clamp(sum(weighted_contribution_i), 0, 100)
```

Weights are normalized before use, so `RiskWeights` need not sum to 1.0 — the overall score always stays within bounds regardless of configuration.

### Risk Category

| Score range | Category |
|---|---|
| `< 25` | LOW |
| `25 – <50` | MODERATE |
| `50 – <75` | HIGH |
| `>= 75` | SEVERE |

### Missing Data Handling

The engine never silently fabricates missing data. When a factor's raw value isn't supplied:
- **Vessel age** unknown → documented default score (40), flagged `is_estimated=True`.
- **Predicted delay** with no ML forecast → deadline-buffer proxy (or a neutral default of 50 if no buffer is available either), flagged `is_estimated=True`.
- Every other factor has an explicit mock default in `RiskFactorInput` and is never marked estimated (it's a configured baseline, not a gap).

### Integration

`RiskEngine.assess_voyage()` consumes a `VoyageFeasibilityResult` directly (vessel, route, and deadline buffer), so it slots straight into the matching → feasibility → risk pipeline. `assess_all()` batches this across every feasible vessel, with optional per-vessel `RiskFactorInput` overrides.

> **No ML lives in this module.** `predicted_delay_risk_score` is the only ML-shaped input, and it is always optional and externally supplied — the fallback formula is a clearly labeled placeholder, not a prediction.

---

## Phase 5 — Vessel Ranking

Given the full set of Phase 2 voyage results plus the corresponding Phase 3 cost breakdowns and Phase 4 risk assessments, `RankingEngine.rank()` returns a fully explained `RankedVessel` for every candidate — feasible vessels are scored and ranked; infeasible vessels are structurally excluded.

### Hard Constraints Are Absolute

**A vessel rejected by Phase 1 or Phase 2 is never scored, never ranked, and can never appear in `RankingEngine.feasible()`'s output — regardless of how favorable its raw numbers would have been.** Infeasible vessels are still included in the full result list (for transparency and auditability) but with `rank=None`, `overall_score=None`, and empty component scores.

### Ranking Components (6, each scored 0–100, higher = better)

| Component | Default weight | Scoring method |
|---|---|---|
| Total voyage cost | 0.30 | Batch-relative (cheapest in this batch scores 100) |
| Risk | 0.20 | Batch-relative (lowest risk in this batch scores 100) |
| Deadline buffer | 0.20 | Batch-relative (most buffer in this batch scores 100) |
| Cargo suitability | 0.10 | Absolute — `100 × (cargo.quantity_mt / vessel.cargo_capacity_mt)` |
| Availability | 0.10 | Absolute — linear ramp from 0 (available on the deadline) to 100 (≥30 days lead time) |
| Operational suitability | 0.10 | Absolute — fixed lookup by `vessel.status` (AVAILABLE=100, EN_ROUTE=75, LOADING/DISCHARGING=60) |

**Why the mixed scoring method?** Cost, risk, and deadline buffer have no universal "good" value in isolation — a cost is only cheap *relative to the alternatives being compared*. Cargo suitability, availability, and operational suitability, by contrast, are meaningful properties of a vessel on their own (an AVAILABLE vessel is operationally ready no matter who else is competing). This is a documented methodology choice, always disclosed in each result's `assumptions`.

### Weighting

```
normalized_weight_i = weight_i / sum(all weights)
weighted_contribution_i = normalized_score_i × normalized_weight_i
overall_score = clamp(sum(weighted_contribution_i), 0, 100)
```

Weights are normalized before use, so `RankingWeights` need not sum to 1.0.

### Tie-Breaking

Vessels with an identical `overall_score` are ordered deterministically by `vessel_id` (ascending) — re-running the same inputs always produces the same order.

### Missing Data

`RankingEngine.rank()` **raises `ValueError`** if a feasible vessel has no matching `VoyageCostBreakdown` or `RiskAssessmentResult` — it never fabricates a score from incomplete data. Compute Phase 3 and Phase 4 for every feasible vessel before ranking it.

### Integration

`RankingEngine.rank()` takes the *full* list of Phase 2 `VoyageFeasibilityResult` (feasible and infeasible mixed together) and does the feasible/infeasible split internally, so it slots directly after the matching → feasibility → economics → risk pipeline. Use `RankingEngine.feasible()` for the sorted, ranked shortlist, and `RankingEngine.excluded()` to audit why other vessels didn't make it.

> **No ML, no OR-Tools.** Ranking is a transparent, deterministic weighted sum — not a solver, not a model.

### Known Sharp Edge: Batch-Relative Amplification

Because cost/risk/deadline-buffer are scored *relative to the current batch* (min-max normalized), even a tiny real-world difference gets fully amplified to a 100/0 split when the batch is small. For example, two vessels with deadline buffers of 66.09 and 66.00 days (a 0.09-day difference) will score 100 and 0 respectively on that component if they're the only two candidates — the same 0.09-day gap would barely matter in a batch of 20. This was discovered empirically while building Phase 7's simulation tests (a fuel-price-tripling scenario didn't flip the top recommendation, because a near-invisible buffer difference was dominating the ranking) and is a real characteristic of min-max batch-relative scoring, not a bug. Keep it in mind when reasoning about ranking behavior with very few candidates.

---

## Phase 6 — Charter Decision Engine

Turns Phase 5's ranked shortlist into an actual decision: `BOOK_NOW`, `WAIT`, `SELECT_ALTERNATIVE_VESSEL`, or `SELECT_ALTERNATIVE_ROUTE`.

### Compare, Don't Cascade

**Ranking answers "which candidate is better?"; this engine answers "what should we actually do?"** — and it does so by building *every* relevant alternative and comparing them on one commensurable metric, rather than a priority if/elif chain that could stop before evaluating WAIT just because a vessel switch looked good. Alternatives built:

1. `BOOK_NOW` for every feasible, risk-acceptable vessel on the current route.
2. `WAIT` (re-booking the current route's best vessel later) — **only if** a `FreightForecastInput` is supplied.
3. `BOOK_NOW` for the best vessel on each alternative route, if `RouteCandidate`s are supplied (Phase 8 integration).

Every alternative appears in `DecisionResult.alternatives`, including the ones that lost.

### The Comparison Metric

```
adjusted_cost = total_cost + overall_risk_score × risk_cost_per_point
```

`adjusted_cost` is a *comparison* metric only. `expected_total_cost` on both `DecisionAlternative` and `DecisionResult` is always the real, raw dollar figure — never overwritten by the adjusted value (Rule: preserve raw physical/economic values). With the default `risk_cost_per_point=0.0`, risk acts purely as a hard gate (`max_acceptable_risk_score`) and doesn't affect cost comparisons among gate-passing vessels.

### The Freight Forecast Contract

```python
class FreightForecastInput(BaseModel):
    current_freight_rate_per_mt: float
    predicted_freight_rate_per_mt: float
    forecast_horizon_days: float
    confidence: Optional[float] = None
    lower_bound_per_mt: Optional[float] = None
    upper_bound_per_mt: Optional[float] = None
    source: str = "mock"
```

This is the **one typed shape** this engine understands for "what might the freight rate do if we wait." `fixtures.MOCK_FREIGHT_FORECAST` populates it today; Member 1's real ML model will populate the exact same contract later — no code change required here. Without a forecast, `WAIT` is never even constructed as an alternative; there's no fabricated basis to recommend waiting.

### WAIT's Risk Impact

Waiting shrinks the deadline buffer, which this engine accounts for by **reusing** Phase 4's own `calculate_predicted_delay_risk_fallback()` formula on the smaller post-wait buffer (not duplicating it) and applying the delta to the vessel's already-computed risk score.

### Typed Route Identity

`DecisionResult.selected_route` and every `DecisionAlternative.route` are full `Route` objects — never a bare route-id string used as a dict key. Alternative routes are supplied as `RouteCandidate` (route + its own ranked-vessel shortlist), defined in `multiroute/models.py`.

### Never Selects Infeasible

The decision layer only ever chooses from `RankingEngine.feasible()`'s output. If that's empty, the result is `NO_FEASIBLE_OPTION` with no vessel/route selected.

---

## Phase 7 — What-If Scenario Simulation

`ScenarioSimulator.simulate()` answers "what happens if...?" by applying **one** change to a *copy* of the relevant inputs, re-running Phases 1–4 (never duplicating their formulas), and diffing the result against an untouched baseline.

### Supported Scenarios

| Scenario | What changes |
|---|---|
| `FUEL_PRICE_CHANGE` / `FREIGHT_RATE_CHANGE` | `VoyageCostInput` rate × `multiplier` |
| `VESSEL_DELAY` | `Vessel.available_from` + `additional_days` (departure shifts) |
| `WEATHER_DELAY` | Effective speed reduced so sailing takes `additional_days` longer (same departure); weather risk bumped +20 |
| `PORT_WAITING_INCREASE` | `VoyageCostInput.port_days` + `additional_days` (cost only — Phase 2's ETA doesn't model port waiting) |
| `CONGESTION_INCREASE` | `RiskFactorInput.congestion_risk_score` + `congestion_delta`, clamped [0, 100] |
| `CARGO_QUANTITY_CHANGE` | `Cargo.quantity_mt` × `multiplier` (can flip Phase 1 capacity feasibility) |
| `DEADLINE_CHANGE` | `Cargo.required_arrival_date` + `deadline_shift_days` |
| `VESSEL_UNAVAILABLE` | `Vessel.status` → `UNDER_MAINTENANCE` (hard-excluded by Phase 1) |
| `ALTERNATIVE_VESSEL` / `ALTERNATIVE_ROUTE` | Wholesale substitute, evaluated fresh |

### Baseline Is Never Mutated

Every mutation uses `model_copy(update=...)` to build a new instance; the original `Vessel`/`Cargo`/`Route`/`VoyageCostInput` objects passed in are untouched (verified by dedicated isolation tests that check the original objects' fields after `simulate()` runs).

### Output

`ScenarioResult` carries a `baseline` and `scenario` `ScenarioSnapshot` (feasible, total_cost, cost_per_mt, deadline_buffer_days, overall_risk_score, risk_category), a list of `ScenarioMetricDiff` (absolute + percentage difference per metric), `feasibility_changed`, and — if the caller supplies the rest of the fleet's baseline results — `recommendation_changed` (does the Phase 5 top pick change because of this scenario?).

---

## Phase 8 — Multi-Route Comparison

`MultiRouteEngine.compare()` ranks externally-supplied candidate routes exactly the way Phase 5 ranks vessels — same hard-constraint discipline, same batch-relative + absolute scoring philosophy, one level up.

### RouteCandidate

```python
class RouteCandidate(BaseModel):
    route: Route
    ranked_vessels: list[RankedVessel]       # this route's own Phase 5 output
    risk_results: list[RiskAssessmentResult] # optional, needed for congestion comparison
    emissions_co2_kg: Optional[float] = None # optional, Phase 9 hook
```

This engine does **not** discover or validate routes — it consumes `RouteCandidate`s the caller already built by running the full Phase 1→5 pipeline once per route.

### Optional Data Is Dropped, Not Fabricated

Congestion and emissions are compared **only when every feasible route in the batch supplies that data**; otherwise that component is excluded from the comparison entirely (not defaulted to a fabricated value), and the remaining weights are renormalized.

### The Cheapest Route Never Automatically Wins

Default weights: cost 0.35, risk 0.25, deadline buffer 0.25, congestion 0.10, emissions 0.05 — cost matters most but is capped well below 1.0, so a cheaper-but-riskier or cheaper-but-slower route can lose to a costlier, safer one (tested explicitly).

---

## Phase 9 — Emissions (Optional)

`EmissionsEngine.calculate()` computes CO2 from fuel already consumed (typically `VoyageCostBreakdown.fuel_consumed_mt`).

```
co2_emissions_kg   = fuel_consumed_mt × 1000 × emission_factor_kg_co2_per_kg_fuel
co2_per_tonne_kg   = co2_emissions_kg / cargo_quantity_mt
co2_per_tonne_km_kg = co2_emissions_kg / (cargo_quantity_mt × distance_nm × 1.852)
```

The default `emission_factor_kg_co2_per_kg_fuel = 3.114` is a commonly cited approximate figure for heavy fuel oil — **explicitly not a verified current regulatory value**, and this module makes no IMO CII/EEXI compliance claim of any kind. Emissions are entirely optional; `FinalRecommendationEngine.recommend(compute_emissions=False)` skips this stage.

---

## Phase 10 — Final Orchestration Layer

`FinalRecommendationEngine.recommend()` runs Cargo → Matching → Voyage Feasibility → Economics → Risk → Ranking → Decision → (optional) Emissions in one call and returns a `FinalRecommendation`.

> **Why "orchestration," not "optimization"?** This layer lives in `optimization_engine/optimization/` to match the agreed project structure, but the class is deliberately named `FinalRecommendationEngine`, not `OptimizationEngine` — there is no mathematical optimization problem here (no decision variables, objective function, or constraint set), so no solver (OR-Tools or otherwise) is used or implied. If a genuine optimization problem is defined in the future, it belongs in its own, separately-named module.

### Multi-Route Cargo/Port Matching (a real constraint, not an oversight)

Phase 2's `VoyageFeasibilityEngine` validates that a route's origin **and** destination match the `Cargo` object's own fields exactly — this existing validation is preserved, not weakened. This means a genuinely cross-origin or cross-destination "alternative route" (e.g. sourcing via Singapore instead of Shanghai) needs its **own** matching `Cargo` object:

```python
AlternativeRouteInput(
    route=singapore_to_paradip_route,
    origin_port=singapore_port,
    cargo=cargo_with_singapore_as_origin,  # required when ports differ from the primary
)
```

If `cargo` is omitted and the route's ports don't match the primary cargo, Phase 2 raises a clear `ValueError` rather than silently producing a wrong answer. This is a documented prototype limitation of the *convenience path* only — the underlying `AlternativeRouteInput`/`RouteCandidate` models already support it.

### Never Selects Infeasible

If no feasible vessel/route combination exists anywhere (primary or alternatives), `FinalRecommendation.feasible = False` and `selected_vessel_id`/`selected_route` are both `None` — never a best-effort fallback.

---

## Phase 11 — Integration Contracts

`optimization_engine/integration/contracts.py` defines nine `typing.Protocol` interfaces — structural types, no inheritance required — describing exactly what this engine expects from each other team's system:

| Owner | Protocols |
|---|---|
| Member 2 (Backend & DB) | `VesselProvider`, `PortProvider`, `CargoProvider`, `TariffProvider` |
| Member 4 (Geospatial & AIS) | `RouteProvider`, `AISProvider` |
| Member 1 (AI/ML) | `FreightForecastProvider`, `CongestionForecastProvider`, `DelayForecastProvider` |

`adapters.py` provides mock/demo-only implementations backed by `fixtures.py` — used by the demo and tests, **never** intended as real integrations. `MockAISProvider` always returns `None` (never a fabricated position), since no engine in this codebase reads AIS data yet.

**Verified constraint:** a static AST scan (`tests/test_integration_contracts.py::TestNoForbiddenFrameworkImports`) confirms zero imports of FastAPI, Flask, Django, psycopg2, SQLAlchemy, requests, torch, tensorflow, or sklearn anywhere in `optimization_engine/`.

---

## Phase 12 — Explainability

`ExplainabilityEngine.explain()` answers, for any `FinalRecommendation`:

- **Why this vessel?** — feasibility, deadline buffer, cost/risk vs. the next-best feasible candidate.
- **Why this route?** — comparison against alternative routes, if any were evaluated.
- **Why this action?** — which alternative had the lowest `adjusted_cost`, and by how much.
- **Why not the alternatives?** — every non-winning `DecisionAlternative`, with its actual cost delta or its exclusion reason (e.g. broke the deadline buffer).

Every number quoted is read directly from the `FinalRecommendation`/`RankedVessel`/`DecisionAlternative` objects being explained — **nothing is recomputed independently**, so the explanation cannot contradict the result by construction. Genuine ties are described as ties, not as a false "X is 0.00 higher" non-reason.

---

## How to Run

### Prerequisites

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run Tests

```bash
# Individual phases
python -m pytest tests/test_constraints.py tests/test_matching_engine.py -v   # Phase 1
python -m pytest tests/test_sailing.py tests/test_voyage_engine.py -v         # Phase 2
python -m pytest tests/test_economics.py -v                                  # Phase 3
python -m pytest tests/test_risk.py -v                                       # Phase 4
python -m pytest tests/test_ranking.py -v                                    # Phase 5
python -m pytest tests/test_decision.py -v                                   # Phase 6
python -m pytest tests/test_simulation.py -v                                 # Phase 7
python -m pytest tests/test_multiroute.py -v                                 # Phase 8
python -m pytest tests/test_emissions.py -v                                  # Phase 9
python -m pytest tests/test_optimization.py -v                               # Phase 10
python -m pytest tests/test_integration_contracts.py -v                      # Phase 11
python -m pytest tests/test_explainability.py -v                             # Phase 12
python -m pytest tests/test_robustness.py -v                                 # Phase 13
python -m pytest tests/test_end_to_end.py -v                                 # Phase 14
python -m pytest tests/test_demo.py -v                                       # Phase 15

# Everything at once
python -m pytest tests/ -v
```

> **A note on how these tests were verified during development:** the AI development sandbox used to build this engine had no network access, so `pydantic`/`pytest` could not be installed there. Every test above was verified two ways: (1) `python3 -m py_compile` on every file (a real syntax check), and (2) execution against a small hand-written shim that reimplements just enough of `pydantic.BaseModel` and `pytest` (fixtures, `raises`, `approx`, `parametrize`) to actually run the real test logic. All **338 test cases across 17 files passed against that shim** as of the last full run — but a shim is not the real library. **Run the commands above for the authoritative result before trusting this in production.** Several genuine bugs (not shim artifacts) were caught this way during development — see `BRAIN.md`'s "Recent Work" log for specifics (e.g. a `risk_category` field that was hardcoded to `None` for the WAIT/switch actions, caught only when the demo script was actually executed).

### Run Demo

```bash
python -m examples.demo
```

Shows the complete pipeline (Phases 1–12) for the canonical 75,000 MT iron ore, Shanghai → Paradip, 15 Oct 2026 scenario: rejected vessels with reasons, feasible vessels with ETA, cost/risk/ranking table, every decision alternative considered, the final recommendation, and its full four-part explanation. Every line is clearly mock/demo data.

---

## Architecture

```
Cargo requirement
       │
       ▼
 MatchingEngine  ──────────────────────────────────  Phase 1  (hard constraints)
       │  feasible MatchResults
       ▼
 VoyageFeasibilityEngine  ─────────────────────────  Phase 2  (ETA, deadline buffer)
       │  feasible VoyageFeasibilityResults
       ▼
 VoyageEconomicsEngine  ───────────────────────────  Phase 3  (itemized cost)
       │
       ▼
 RiskEngine  ───────────────────────────────────────  Phase 4  (0-100 risk score)
       │
       ▼
 RankingEngine  ────────────────────────────────────  Phase 5  (weighted multi-criteria)
       │  RankedVessel list (feasible-only, ranked)
       ▼
 DecisionEngine  ───────────────────────────────────  Phase 6  (compares every alternative)
       │                                       ▲
       │                              RouteCandidate list (optional)
       │                                       │
       │                          MultiRouteEngine  ─  Phase 8  (route comparison)
       ▼
 EmissionsEngine (optional)  ───────────────────────  Phase 9
       │
       ▼
 FinalRecommendationEngine  ────────────────────────  Phase 10 (orchestration, not a solver)
       │  FinalRecommendation
       ▼
 ExplainabilityEngine  ─────────────────────────────  Phase 12 (why vessel/route/action/not-alt)


                     ScenarioSimulator  ────────────  Phase 7  (re-runs Phases 1-4 on a
                     (side-channel: baseline vs           modified copy; never touches
                      scenario comparison)                the live pipeline above)
```

All phases are independently importable and independently tested; `FinalRecommendationEngine` is a convenience orchestrator, not a required entry point — any phase's engine can be used standalone.

### Integration With Other Teams (Phase 11 Contracts)

The engine is **data-source agnostic** — every entry point takes typed Pydantic models as arguments, never a URL, connection string, or vendor SDK object. `optimization_engine/integration/contracts.py` defines the exact `Protocol` each team's real system should satisfy; `adapters.py`'s mock implementations (backed by `fixtures.py`) show what "satisfying the contract" looks like today, for demo/test purposes only.

```
Member 2 (Backend)     →  VesselProvider, PortProvider, CargoProvider, TariffProvider
                        →  domain models (Vessel, Port, Cargo) / VoyageCostInput
Member 4 (Geospatial)  →  RouteProvider, AISProvider
                        →  Route (real distance_nm) / vessel position (currently unused)
Member 1 (ML)          →  FreightForecastProvider, CongestionForecastProvider, DelayForecastProvider
                        →  FreightForecastInput / congestion_risk_score / predicted_delay_risk_score
```

Every one of those fields already has a documented mock default and a clearly-flagged "estimated, not fabricated" fallback — plugging in a real provider requires no change to any engine's logic, only to which object gets passed in.

---

## License

Internal project — Smart India Hackathon 2026.
