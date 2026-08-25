# Decision log — ENA ABM v0.4 checkpoint

## D-021 — Cost is separate from effectiveness

**Decision before implementation:** Keep `direct_action_cost` and
`referral_action_cost` outside the adoption rule. Normalize direct cost to 1
and interpret referral cost as r.

**Observed:** Matched cost-only changes leave utility and adoption probability
unchanged.

## D-022 — An attempt is charged only after a feasible source or target exists

**Decision before implementation:** A direct target or adopted referral source
must exist before an attempt begins. A referral source does not need to be
known in advance to possess an eligible neighbor.

**Observed:** No adopted referrer produces an unavailable-opportunity record
without cost. An adopted but isolated referrer produces a paid failed attempt.

## D-023 — Explicit exposure process

**Decision before implementation:** Separate direct effective exposure from
the referral stages of request acceptance, eligible-neighbor availability,
and effective introduction. Limit every attempt to one exposure.

**Provisional diagnostic values:** Direct exposure 0.512; referral stages
0.80, 0.80, and 0.80, whose product is 0.512 conditional on structural
opportunity. These are neutral diagnostic values, not empirical estimates.

**Observed:** The automated neutral case produces identical behavioral
outcomes when all mechanisms and targets are equivalent.

## D-024 — Primary and robustness accounting conventions

**Decision before implementation:** Use full expected cost at attempt
initiation as primary. Compare equal 0.25 stage shares as a diagnostic
robustness convention. Stop if coarse-grid r* differs by at least 0.25.

**Observed:** Upfront r*=1.00 and staged r*=1.25 on the predefined coarse
baseline grid. The difference equals 0.25.

**Status:** Scientific stop condition triggered. The complete condition map
and refined thresholds were not executed.

## Pending joint decision

Decide whether the article should:

1. retain upfront expected cost as the primary estimand;
2. make staged cost primary after empirical activity-share evidence; or
3. report both as separate estimands and partially identify r*.

No assumption has been changed silently after the stop gate.
