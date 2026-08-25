# Preregistered Design v0.5

**Frozen before execution:** 2026-07-25  
**Scientific status:** main theoretical computational experiment with
diagnostic, non-calibrated parameters.

## Research question

Under what combinations of market sociality, network structure, consumer
conditions, resources, and referral opportunities does one-to-one referral
activation equal or outperform direct outreach under an equal allocated
budget?

## Model boundary

The v0.4 behavioral and cost architecture is frozen. Version 0.5 adds no new
behavioral mechanism. It compares only direct outreach and one-to-one
referrals. It excludes promoters, mass referrals, events, negative WOM,
combined strategies, incentives as behavioral mechanisms, Consumat logics,
and empirical calibration.

All values are theoretical diagnostic ranges. Results may identify internal
model regularities and boundary conditions, but not population estimates or
empirically expected effect sizes.

## Primary estimands

For profile \(x\) and relative referral cost \(r=C_R/C_D\):

\[
\Delta(r\mid x)=E[Y_R(r\mid x)-Y_D(x)].
\]

The primary outcome \(Y\) is new adoptions excluding seed customers. The
primary threshold is the greatest evaluated \(r\) with nonnegative mean paired
difference. The conservative and probability thresholds retain their v0.4
definitions. Profiles without a competitive region, with competitiveness at
the upper boundary, or with multiple crossings are reported without forcing a
single threshold.

## Main design

The main design contains 96 deterministic stratified Latin-hypercube profiles.
The three network structures are balanced at 32 profiles each. Nine factors
use the ranges screened in v0.3:

- market sociality;
- fit mean;
- status-quo satisfaction mean;
- initial uncertainty mean;
- adoption intercept;
- individual coefficient;
- social coefficient;
- allocated budget; and
- initial seed adopters.

The design is space-filling rather than a full factorial. It preserves the
full screened ranges and retains low-adoption, zero-adoption, extinction, and
resource-constrained runs.

## Relative cost and pairing

- \(C_D=1\).
- \(r\) is searched from 0.25 to 3.00 on a 0.25 grid.
- Every crossing bracket is refined to 0.05.
- The primary convention charges the full expected cost at attempt initiation.
- Staged accounting remains secondary.
- Each cell uses 400 paired replications.
- Networks, attributes, seeds, and random streams are paired across
  strategies and all \(r\) values within a profile-replicate.

## Confirmatory comparisons

The predeclared summaries are:

1. the distribution and finite range of \(r^*(x)\);
2. the share of profiles where referrals is competitive at \(r=1.00\);
3. the share competitive at the v0.4 baseline \(r=1.20\);
4. mean paired adoption differences and 95% intervals at those cost ratios;
5. takeoff, extinction, exposure, conversion, cascade, and timing differences;
6. network-stratified threshold distributions; and
7. the conditions associated with finite, absent, or boundary-censored
   competitive regions.

No single universal \(r^*\) will be inferred from the profile distribution.

## Sensitivity analysis

Sensitivity is separated from stochastic uncertainty:

- bootstrap distributions quantify within-profile Monte Carlo uncertainty;
- Spearman associations describe monotonic factor-threshold relations;
- a deterministic random-forest emulator provides nonlinear permutation
  importance and cross-validated predictive accuracy;
- shallow decision trees provide descriptive rules for competitiveness at
  \(r=1.00\) and \(r=1.20\).

Emulator importance is not interpreted as a causal effect.

## Robustness

Predeclared analyses cover:

- eight exposure-process regimes in each network structure;
- nine contexts under upfront versus staged accounting;
- population size, degree, rewiring, and network form;
- takeoff thresholds of 5%, 10%, 15%, and 20%; and
- extinction quiet periods of 3, 5, and 10 ticks.

## Interpretation and stop rules

Interpretation stops if:

- more than 10% of main profiles show multiple crossings;
- fewer than 50% of profiles yield an interpretable competitive region;
- bootstrap threshold width exceeds 0.50 for a majority of finite profiles;
- budget residuals exceed 10% and determine threshold ordering;
- upfront and staged accounting differ by at least 0.25 across enough central
  contexts to reverse the substantive conclusion;
- a process probability mechanically determines the comparison so strongly
  that no conditional interpretation remains; or
- independent reproduction does not match.

An individual boundary condition may lack a competitive region without
stopping the study; it is a theoretical result. Any unplanned design change
must be recorded before re-execution.
