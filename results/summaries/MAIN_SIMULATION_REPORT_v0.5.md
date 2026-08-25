# Main Simulation Study v0.5

> Theoretical computational experiment. Parameters are diagnostic and
> are not empirically calibrated.

## Design

- 96 stratified profiles.
- 400 paired replications per profile-cost cell.
- Three balanced network structures.
- Relative referral cost searched from 0.25 to 3.00 and refined to 0.05.
- 972,800 paired result rows across main and robustness analyses.

## Main threshold distribution

- Interpretable finite thresholds: 91/96 (94.8%).
- Median r*: 1.05.
- Interquartile range: [1.00, 1.20].
- Finite range: [0.85, 2.80].
- Multiple crossings: 0.
- No competitive tested region: 4.
- Median bootstrap interval width: 0.10.

## Equal-cost and v0.4-threshold comparisons

At r=1.00, referrals is competitive in 77.1% of profiles. Mean profile-level Δ is 0.49 adoptions (direct 6.58; referral 7.07).

At r=1.20, referrals is competitive in 26.0% of profiles. Mean profile-level Δ is -0.81 adoptions (direct 6.58; referral 5.77).

These percentages describe the registered theoretical design space, not
the prevalence of real markets.

## Network structure

| Network | Finite profiles | Median r* | IQR |
|---|---:|---:|---:|
| preferential attachment | 31/32 | 1.05 | [1.00, 1.12] |
| ring | 31/32 | 1.05 | [1.00, 1.23] |
| small world | 29/32 | 1.05 | [0.95, 1.35] |

## Global sensitivity

The nonlinear threshold emulator used 91 finite profiles. Five-fold cross-validated R² was 0.20 (SD 0.84). Permutation importance
and rank associations are reported in separate tables. These are
descriptive model sensitivities, not causal estimates.

## Robustness

Exposure-process conditions without a competitive tested region: preferential_attachment:acceptance_low, preferential_attachment:direct_exposure_advantage, preferential_attachment:eligible_neighbors_none, ring:acceptance_low, ring:eligible_neighbors_none, small_world:acceptance_low, small_world:eligible_neighbors_none.
The median absolute staged-versus-upfront threshold difference was 0.10; 1/9 predeclared contexts differed by at least 0.25.
Structural robustness produced 9 finite thresholds across 9 contexts.
Dynamic-definition robustness evaluated 24 condition-cost cells; adoption counts are unaffected by these
definitions, while takeoff and extinction labels vary as intended.

## Interpretation gate

Interpretation blocked: **false**.
- multiple crossings: false.
- insufficient interpretable profiles: false.
- widespread threshold instability: false.
- budget rounding dominance: false.
- accounting convention reverses central conclusion: false.

## Scientific conclusion

Referrals is not unconditionally superior. Its relative advantage
depends jointly on the cost ratio, market and consumer parameters,
network structure, resource availability, and the probability that
the referral chain produces an effective exposure. The model identifies
conditional theoretical regions; empirical work would be required to
locate real firms or markets inside those regions.
