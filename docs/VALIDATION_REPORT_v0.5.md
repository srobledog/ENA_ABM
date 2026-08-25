# Validation Report v0.5

## Status

Version 0.5 is complete as a main theoretical computational experiment with
diagnostic parameters. It is not empirically calibrated.

## Frozen architecture

- All 15 v0.4 model-source files match their registered SHA-256 hashes.
- The inherited 59 tests and five v0.5 design tests pass.
- No Consumat logic, promoter, event, mass referral, negative WOM, combined
  strategy, or new adoption mechanism was added.
- Full expected cost at attempt initiation remains primary.
- Stage-based realized cost remains secondary.

## Execution

- 96 deterministic stratified profiles.
- Three network structures, balanced at 32 profiles each.
- Nine jointly varied parameters from the v0.3 screened ranges.
- 400 paired replications per profile-cost cell.
- \(r\in[0.25,3.00]\), coarse step 0.25, crossing refinement to 0.05.
- 972,800 paired rows in each independent reproduction.

## Main thresholds

| Indicator | Result |
|---|---:|
| Finite interpretable profiles | 91/96 |
| Median primary \(r^*\) | 1.05 |
| Primary \(r^*\) IQR | [1.00, 1.20] |
| Finite primary range | [0.85, 2.80] |
| Profiles without a competitive tested region | 4 |
| Profiles competitive through \(r=3.00\) | 1 |
| Multiple crossings | 0 |
| Median bootstrap interval width | 0.10 |

Three high-threshold profiles have wider bootstrap intervals, and the
upper-bound profile is censored. These cases are retained and flagged rather
than used to assert a precise universal upper threshold.

## Registered cost contrasts

- At \(r=1.00\), referrals is competitive in 77.1% of registered profiles.
  Mean profile-level \(\Delta=+0.49\) adoptions.
- At \(r=1.20\), referrals is competitive in 26.0% of profiles.
  Mean profile-level \(\Delta=-0.81\) adoptions.

These proportions characterize the simulated design space and are not
estimates of real-market prevalence.

## Sensitivity

Market sociality, uncertainty, and the social coefficient have the strongest
rank associations with finite \(r^*\). The nonlinear emulator assigns the
largest permutation importance to the same three variables, but its
cross-validated predictive performance is weak and variable. Emulator-based
rules are therefore descriptive only.

## Process robustness

Low acceptance and absence of eligible neighbors remove the competitive region
in all three network structures. A direct-exposure advantage also removes it
under preferential attachment and lowers it under ring and small-world
networks. Referral-exposure advantage, high acceptance, and abundant eligible
neighbors increase the threshold.

## Cost-accounting robustness

The median absolute threshold difference between staged and upfront cost is
0.10. The abundant-budget context differs by 0.25; the other eight contexts
remain below the material criterion. The convention does not reverse the
central main-study conclusion.

## Structural and dynamic robustness

All nine structural contexts have finite thresholds, ranging from 1.00 for the
small market to 1.25 for the low-degree, ring, large-market, and zero-rewiring
contexts. Alternative takeoff and quiet-period definitions change takeoff and
extinction labels as intended but not adoption counts or the primary cost
comparison.

## Stopping conditions

No interpretation blocker was activated:

- multiple-crossing share: 0;
- finite interpretable share: 94.8%;
- bootstrap width above 0.50: 3.2%;
- budget rounding does not dominate;
- accounting does not reverse the conclusion; and
- independent reproduction succeeds.

## Reproducibility

Two complete executions produced 972,800 paired rows each. All decompressed raw
data hashes matched immediately. After normalizing non-scientific gzip header
timestamps, all 34 principal outputs were byte-identical.

## Interpretation boundary

The study establishes conditional theoretical regularities inside the
registered diagnostic design. It does not establish empirical costs,
population frequencies, or expected effect sizes for real firms. Empirical
calibration remains a future extension rather than a requirement for drafting
the current theoretical article.
