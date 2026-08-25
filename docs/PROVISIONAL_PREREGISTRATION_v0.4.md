# Provisional Preregistration v0.4

**Status:** updated for joint review. Do not execute as the definitive article
experiment.

## Research question

Under what market, network, and referral-opportunity conditions does referral
activation remain competitive with direct outreach after accounting for the
relative total expected cost of an initiated attempt?

## Primary architecture

- Fairness criterion: equal allocated budget.
- Direct-attempt cost: \(C_D=1\).
- Referral-attempt cost: \(C_R=r\).
- Cost deduction: full expected cost when a feasible attempt begins.
- Failed attempts: consume full cost.
- Unavailable source: no attempt and no cost.
- One attempt: at most one effective exposure.

Staged accounting is a secondary robustness estimand only.

## Primary process sequence

Resource availability, strategy, eligible source or target, attempt and cost,
response or acceptance, effective exposure, evaluation, and possible
adoption.

The referral path separately records source availability, request acceptance,
eligible-neighbor availability, effective introduction, evaluation, and
adoption.

## Primary outcome and thresholds

The primary outcome is new adoptions excluding seeds.

\[
\Delta(r\mid x)=E[Y_R(r\mid x)-Y_D(x)]
\]

Primary \(r^*\) is the largest evaluated \(r\) with nonnegative mean paired
difference. Conservative, probability, and allocated-budget efficiency
thresholds retain their v0.4 definitions and will not be selected
post-hoc.

## Cost grid and crossing procedure

- Initial grid: 0.25 to 3.00 in increments of 0.25.
- Refinement: every sign-change bracket to 0.05.
- Multiple crossings: report competitive regions, not one threshold.
- No crossing: report absence or boundary censoring.
- Material nonmonotonicity: stop and review.

## Pairing and replications

Networks, consumer attributes, seed customers, and random streams are paired
across strategies. The v0.4 precision pilot selects 400 paired replications
per retained condition because 200 did not satisfy the threshold-stability
criterion when doubled.

The definitive experiment will retain 400 unless a new predeclared precision
pilot demonstrates that a different count is required for the final retained
design.

## Experimental design

Use an efficient design informed by the v0.3 Morris ranking. Priority factors
are:

- market sociality;
- adoption intercept;
- budget;
- status-quo satisfaction;
- fit;
- uncertainty;
- individual and social coefficients; and
- seed availability.

Network structure remains a primary design factor. Credibility and information
reduction remain theoretical robustness factors even though their Morris
effects were smaller.

Do not use a full factorial unless its computational and inferential value is
demonstrated. The 26-condition v0.4 map is validation, not the main design.

## Exposure-process robustness

Explicitly evaluate:

- equal conditional exposure;
- direct exposure advantage;
- referral exposure advantage;
- low and high acceptance;
- absent and abundant eligible neighbors; and
- absent, scarce, and abundant referrers.

All values remain diagnostic until empirical calibration.

## Statistical analysis

- Mean paired adoption difference with 95% interval.
- Median and 10th/90th percentiles.
- \(P(Y_R>Y_D)\) and equality probability.
- Monte Carlo standard error.
- Bootstrap distribution of \(r^*\).
- Separate stochastic uncertainty from factor sensitivity.
- Inspect zero inflation, heteroskedasticity, and budget plateaus.
- Report effect magnitudes and uncertainty, not isolated significance.

## Robustness

- Staged cost accounting with empirically justified shares when available.
- Takeoff thresholds 5%, 10%, 15%, and 20%.
- Quiet periods 3, 5, and 10 ticks.
- Credibility contrasts.
- Alternative network sizes, degrees, and rewiring.
- Alternative budget levels and residual-budget diagnostics.
- Global sensitivity for Morris-prioritized parameters.

## Empirical cost evidence

Future interviews, time records, or firm logs will populate the v0.4 activity-
costing workbook. The resulting \(C_D\), \(C_R\), and interval for \(r\) will be
compared with the modeled competitive regions. No value of entrepreneurial
time is fixed in the preregistration.

## Exclusions

Exclude only corrupted runs, invariant failures, unregistered configurations,
or failed pairing. Retain zero adoption, extinction, unused resources, failed
attempts, and unavailable referral opportunities.

## Stop rules

Stop before the definitive experiment or any behavioral extension if:

- empirical stage shares are required but unavailable;
- exposure parameters determine the comparison arbitrarily;
- accounting conventions differ materially in retained main conditions;
- multiple crossings or unstable regions appear;
- budget rounding dominates the threshold;
- reproducibility fails; or
- new mechanisms require a separate model version.

The current abundant-budget staged-accounting difference of 0.25 keeps the
Consumat extension on hold.
