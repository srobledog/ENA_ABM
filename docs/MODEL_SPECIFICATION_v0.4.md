# Model Specification v0.4

## Entrepreneurial Network Activation ABM

**Version:** 0.4  
**Scientific status:** cost, exposure, and break-even validation phase  
**Interpretation boundary:** all parameter values and results in this version
are diagnostic. They are not calibrated estimates or findings from the
definitive article experiment.

## 1. Validation question

For experimental condition \(x\), what is the maximum referral-attempt cost
relative to direct outreach for which referrals remains competitive under an
equal budget?

\[
\Delta(r\mid x)=E[Y_R(r\mid x)-Y_D(x)]
\]

\[
r^*(x)=\sup\{r:\Delta(r\mid x)\geq 0\}
\]

The primary outcome \(Y\) is the number of new adopters excluding seed
customers.

## 2. Scope and exclusions

Version 0.4 compares only:

- direct outreach; and
- one-to-one referral activation.

It does not implement Consumat decision logics, promoters, events,
presentations, strategic follow-up, negative WOM, combined strategies,
multiple referrals per action, campaigns, incentives as a behavioral
mechanism, or NetLogo.

## 3. Cost architecture

For strategy \(s\):

\[
C_s=V_TT_s+M_s
\]

where \(T_s\) is entrepreneurial time, \(V_T\) is the economic value of one
time unit, and \(M_s\) is monetary expenditure.

Direct outreach is decomposed into search, contact, coordination, and
follow-up. Referral activation is decomposed into identifying a referrer,
requesting the referral, coordinating the introduction, follow-up, and any
incentive. In the current incentive-free model, incentive cost equals zero.

The normalized model uses:

\[
C_D=1,\qquad C_R=r
\]

Here \(r\) is a cost ratio only. It does not change acceptance, exposure,
credibility, uncertainty, utility, or adoption probability.

## 4. Two cost layers

### 4.1 Normalized model layer

The primary convention charges the full expected action cost when a feasible
attempt begins. A failed attempt consumes the full cost. If no eligible direct
target or adopted referral source exists, no attempt begins and no cost is
charged.

### 4.2 Empirical activity-costing layer

The workbook `EMPIRICAL_ACTIVITY_COSTING_TEMPLATE_v0.4.xlsx` estimates
\(C_D\), \(C_R\), and an empirical interval for \(r\) from future time records,
interviews, or business logs. No empirical values are supplied in v0.4.

## 5. Activation process

Every entrepreneurial action follows:

1. resource availability;
2. strategy selection;
3. eligible target or source identification;
4. attempt initiation and cost deduction;
5. response or request acceptance;
6. effective exposure;
7. individual evaluation; and
8. possible adoption.

One attempt can create at most one effective exposure.

### 5.1 Direct outreach

A feasible target is selected, the attempt begins, and the configured direct
effective-exposure Bernoulli process is evaluated. Failed contact is a paid
attempt with no exposure.

### 5.2 Referrals

An adopted referrer must exist before the attempt begins. After initiation,
the model evaluates, in order:

1. referral-request acceptance;
2. eligible-neighbor availability;
3. effective introduction; and
4. evaluation and possible adoption.

A rejected request, lack of an eligible neighbor after initiation, or failed
introduction is a paid failed attempt under the primary convention. Absence of
any adopted referrer is an unavailable opportunity, not an attempt.

## 6. Diagnostic exposure parameters

The baseline uses:

- direct effective exposure: 0.512;
- referral acceptance: 0.80;
- eligible-neighbor availability: 0.80; and
- effective introduction: 0.80.

The conditional referral product is \(0.8^3=0.512\). These values create a
neutral diagnostic comparison of conditional process probabilities. They are
not empirical estimates. Structural opportunity remains strategy-specific and
is measured separately.

The controlled two-person equality test proves label invariance when costs,
targets, opportunities, credibility, and effective-exposure mechanisms are
fully equivalent.

## 7. Resource accounting

The model enforces:

- nonnegative budget;
- no attempt when the start cost is unaffordable;
- full cost for failed attempts under the primary convention;
- no cost for an unavailable source opportunity;
- exact reconciliation of initial budget, cost events, and unused budget;
- explicit residual-budget recording; and
- stage-level cost records.

The secondary staged convention charges only activities reached. Its default
diagnostic shares are 0.25 for each of four activities. These shares are not
empirical estimates.

## 8. Recorded process and outcome metrics

Separate records are maintained for eligible sources, unavailable
opportunities, attempts, failures, accepted requests, eligible neighbors,
effective introductions, exposures, evaluations, and adoptions.

Cost metrics include spent and unused resources, cost per attempt, cost per
effective exposure, cost per new adopter, exposures per attempt, adoption per
exposure, and adoption per allocated or spent budget unit.

Dynamic metrics include time to first adoption, mean time to adoption,
takeoff, extinction, cascade reach, largest referral cascade, and maximum
cascade depth.

## 9. Break-even estimands

The definitions were fixed before the diagnostic map:

- **Primary:** largest tested \(r\) with mean paired
  \(\Delta(r\mid x)\geq0\).
- **Conservative:** largest tested \(r\) whose 95% lower confidence limit for
  \(\Delta\) is nonnegative.
- **Probability:** largest tested \(r\) with
  \(P(Y_R>Y_D)\geq0.50\).
- **Efficiency:** largest tested \(r\) with nonnegative difference in
  adoptions per allocated budget unit.

Because both strategies receive the same allocated budget, the allocated-
budget efficiency threshold is algebraically aligned with the primary
adoption threshold. Spent-budget efficiency remains a separate diagnostic.

## 10. Estimation

The initial grid is \(r\in[0.25,3.00]\) in increments of 0.25. Every sign-
change bracket is refined to 0.05. Networks, attributes, seed customers, and
random streams are paired across strategies. The Monte Carlo precision pilot
selected 400 paired replications per retained condition.

The reduced diagnostic design contains 26 one-factor-at-a-time or boundary
conditions informed by the v0.3 Morris screening. It covers network
structure, market sociality, uncertainty, status-quo satisfaction, social
influence, source and neighbor availability, acceptance, exposure,
credibility, budget, and population size.

## 11. Identification safeguards

A single threshold is not reported when:

- no competitive region occurs in the tested range;
- competitiveness persists through the upper boundary;
- more than one crossing occurs; or
- a material upward jump exceeds its paired Monte Carlo uncertainty
  allowance.

Bootstrap resampling of paired replicates quantifies threshold stability.

## 12. Version status

All 59 automated tests pass. The primary map has no multiple crossings or
material upward jumps. Three boundary conditions have no stable competitive
region in the tested range: no referrers, no eligible neighbors, and low
request acceptance.

The model is not approved for a Consumat extension because staged accounting
changes the abundant-budget threshold by 0.25 and the stage shares lack
empirical support.
