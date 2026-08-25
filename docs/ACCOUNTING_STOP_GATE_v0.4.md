# Cost-accounting stop gate — ENA ABM v0.4

## Status

The v0.4 workflow is paused at a predefined scientific stop condition. These
results are diagnostic model validation, not evidence for the article.

## Question tested

Does the estimated referral cost threshold depend substantially on whether the
model:

1. charges the full expected action cost when an attempt starts; or
2. charges activity costs only when the corresponding stage is reached?

The predefined stop threshold was an absolute difference of at least 0.25 in
the coarse-grid estimate of the primary break-even ratio.

## Diagnostic design

- Baseline network: small world, 100 consumers, mean degree 6.
- Market sociality: 0.50.
- Seed customers: 3.
- Equal budget: 40 normalized units.
- Direct action cost: 1.
- Referral relative cost grid: 0.25 to 3.00 in increments of 0.25.
- Replications: 50 paired replications at every grid point.
- Same network, consumer attributes, seed customers, and master seed within
  every direct–referral pair.
- Neutral conditional exposure probabilities:
  - Direct effective exposure: 0.512.
  - Referral acceptance: 0.80.
  - Referral eligible-neighbor availability: 0.80.
  - Referral effective introduction: 0.80.
  - Conditional referral exposure product: 0.512.
- Equal source credibility: 0.60.

The probabilities are diagnostic values. They are not empirical estimates.

## Observed coarse-grid thresholds

| Accounting convention | Largest tested r with mean Δ ≥ 0 |
|---|---:|
| Full expected cost at attempt initiation | 1.00 |
| Cost charged by reached stage | 1.25 |

The observed difference is 0.25. The predefined stop condition is therefore
triggered.

The first convention produced mean referral-minus-direct differences of 1.26
at r=1.00 and -0.38 at r=1.25. The staged convention produced 2.88 at r=1.00
and 0.34 at r=1.25, declining to -1.16 at r=1.50.

## Interpretation

The difference is not caused by cost entering adoption utility. Cost remains
separate from acceptance, exposure, credibility, uncertainty, and adoption.
It arises because failed referral requests consume only the activities reached
under staged accounting, which permits additional attempts within the same
budget.

The result does not yet establish either convention as correct. It identifies
a scientific decision that must be resolved before the complete map of r*
conditions is estimated.

## Decision required

Choose one of the following routes before continuing:

1. Retain full expected cost at attempt initiation as the primary estimand and
   keep staged costing as a robustness analysis with an explicit sensitivity
   warning.
2. Treat staged activities as the primary economic mechanism and obtain or
   elicit empirical activity shares before estimating the definitive map.
3. Report both conventions as separate estimands and define a partial-
   identification interval for r* rather than one primary threshold.

No final article experiment, full condition map, or Consumat extension was
executed after this gate.
