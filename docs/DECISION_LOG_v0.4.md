# Decision Log — ENA ABM v0.4

## D-021 — Cost is separate from effectiveness

**Decision:** Normalize direct cost to 1 and interpret referral cost as \(r\).
Cost remains outside process probabilities, credibility, uncertainty, utility,
and adoption.

**Observed:** Cost-only changes leave matched utility and adoption probability
unchanged.

## D-022 — Feasible source or target precedes an attempt

**Decision:** A direct target or adopted referral source must exist before an
attempt begins. Neighbor availability is evaluated after a referral request.

**Observed:** No referrer creates an unavailable-opportunity record without
cost. A referrer that fails to yield an eligible neighbor produces a paid
failed attempt.

## D-023 — Explicit exposure process

**Decision:** Separate direct exposure and the referral stages of acceptance,
neighbor availability, and introduction. Limit one attempt to one exposure.

**Diagnostic values:** direct 0.512; referral 0.80, 0.80, and 0.80. Their
conditional products are equal.

**Observed:** The controlled neutral equality case is label invariant.

## D-024 — Accounting stop gate

**Decision before implementation:** Use upfront expected cost as primary and
equal 0.25 staged shares as robustness. Stop if the coarse \(r^*\) gap reaches
0.25.

**Observed:** With 50 replications, coarse estimates were 1.00 and 1.25. The
stop gate was triggered.

## D-025 — Joint authorization after stop gate

**User decision:** Continue with full expected cost at attempt initiation as
the primary architecture and staged costing as a secondary robustness
analysis.

**Consequence:** Refine both thresholds, run the precision pilot, construct
the reduced condition map, and retain an explicit accounting-sensitivity
warning.

## D-026 — Replication count

**Predeclared criteria:** bracketing MCSE no greater than 0.30, probability
MCSE no greater than 0.04, and threshold stability within 0.05 when doubled.

**Observed:** 200 met the MCSE criteria but both accounting thresholds changed
0.05 at 400.

**Decision:** Use 400 paired replications for the v0.4 diagnostic map.

## D-027 — Reduced condition design

**Decision:** Use 26 one-factor-at-a-time and boundary conditions informed by
Morris rather than a full factorial.

**Observed:** Twenty-three conditions contain one interpretable competitive
region. Three contain none. No multiple crossing or material upward jump
occurs.

## D-028 — Threshold uncertainty

**Decision:** Quantify \(r^*\) with 500 paired-replicate bootstrap samples.

**Observed:** Baseline median 1.20, interval [1.10, 1.25]. Most condition
intervals are 0.05–0.15 wide; four reach 0.25–0.30.

## D-029 — Budget rounding

**Decision:** Report residual budget and attempts at each primary threshold.

**Observed:** Mean residual share is at most 3.75% and never finances another
full referral attempt. No rounding-driven multiple crossing occurs.

## D-030 — Refined accounting robustness

**Observed:** The refined baseline gap falls to 0.05. The abundant-budget gap
remains 0.25.

**Decision:** Keep upfront expected cost primary. Do not interpret the staged
estimand economically until stage shares are supported by activity-cost
evidence.

## D-031 — Consumat readiness

**Decision:** Do not add Consumat logics yet.

**Reason:** The primary map is stable, but the abundant-budget accounting
sensitivity and absence of empirical activity shares remain unresolved.

## Pending decisions

- Economic value of entrepreneurial time.
- Empirical stage shares and their uncertainty.
- Final efficient design for the article experiment.
- Whether abundant-budget staged accounting remains a main robustness
  condition after empirical costing.

No central assumption was changed silently.
