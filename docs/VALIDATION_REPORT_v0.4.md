# Scientific Validation Report v0.4

## Status

This report documents software verification and diagnostic model validation.
It is not the definitive experiment for the article.

## 1. Authorized accounting decision

The full expected cost charged at attempt initiation is the primary
architecture. Cost charged by reached stages is retained as a secondary
robustness estimand. This decision preserves \(r\) as the total expected cost
of one initiated referral attempt.

## 2. Automated verification

The complete suite contains 59 passing tests:

- 35 inherited or adapted v0.3 tests;
- 19 cost-and-exposure architecture tests; and
- 5 break-even analysis tests.

The tests cover probability bounds, simultaneous updating, paired
initialization, fixed-seed determinism, budget conservation, failed attempts,
unavailable opportunities, stage accounting, one-exposure-per-attempt,
neutral equivalence, threshold definitions, refinement, and multiple-crossing
detection.

## 3. Monte Carlo precision pilot

The predeclared criteria were:

- paired-difference MCSE at the crossing no greater than 0.30;
- worst-case probability MCSE no greater than 0.04; and
- \(r^*\) stable within 0.05 when the sample is doubled.

Although 200 replications met the two MCSE criteria, both accounting
conventions moved by 0.05 between 200 and 400. Therefore, 400 paired
replications were selected.

At 400 replications:

| Accounting | Primary \(r^*\) | Conservative \(r^*\) | Probability \(r^*\) | Bracketing MCSE |
|---|---:|---:|---:|---:|
| Upfront expected | 1.20 | 1.10 | 1.10 | 0.133 |
| Staged | 1.25 | 1.20 | 1.15 | 0.140 |

## 4. Baseline refined curve

Under upfront expected cost:

- at \(r=1.10\), mean \(\Delta=0.61\), 95% CI
  \([0.35,0.87]\);
- at \(r=1.15\), mean \(\Delta=0.19\), 95% CI
  \([-0.07,0.45]\);
- at \(r=1.20\), mean \(\Delta=0.01\), 95% CI
  \([-0.25,0.27]\); and
- at \(r=1.25\), mean \(\Delta=-0.19\), 95% CI
  \([-0.45,0.07]\).

The bootstrap median is \(r^*=1.20\), with percentile interval
\([1.10,1.25]\). The conservative threshold is 1.10.

## 5. Condition map

Twenty-three of 26 conditions contain a competitive region inside the tested
range. Their primary thresholds range from:

- 0.70 when direct effective exposure is more probable; to
- 1.65 when referral effective exposure is more probable.

High market sociality produces \(r^*=1.40\); absence of social influence
produces \(r^*=0.95\). Abundant eligible neighbors produce \(r^*=1.45\), while
high acceptance produces \(r^*=1.40\).

No competitive region is identified for:

- no adopted referrer;
- zero eligible-neighbor availability; and
- referral acceptance of 0.40.

For the low-acceptance case, 99.8% of 500 threshold bootstrap samples also
contain no competitive region. The other two cases produce none in every
bootstrap sample.

## 6. Curve diagnostics

Across the primary map:

- no condition has multiple crossings;
- no condition has a material upward jump;
- no competitive curve reaches the upper \(r=3.00\) boundary; and
- all reported single thresholds end inside the tested interval.

Bootstrap interval width is 0.05–0.15 for most conditions. It reaches 0.25–
0.30 for the ring, small market, scarce referrers, and low uncertainty, so
those thresholds require more cautious interpretation.

## 7. Budget discreteness

At the primary thresholds, mean unused referral budget is below the cost of
one additional referral attempt in every interpretable condition. The largest
mean residual share is 3.75% in the scarce-budget condition. The baseline
residual share is 1.0%.

Budget discreteness creates plateaus but does not generate multiple crossings
or material nonmonotonicity in the diagnostic map.

## 8. Accounting robustness

After refinement and 400 replications, the baseline difference between
accounting conventions is 0.05 rather than the 0.25 observed in the original
50-replication coarse gate.

Among seven selected robustness conditions, the staged-minus-upfront
threshold difference is:

- 0.00 for scarce referrers;
- 0.05 for the baseline;
- 0.10 for scarce budget, abundant referrers, and high sociality; and
- 0.25 for abundant budget.

The abundant-budget condition therefore retains the predefined material
accounting sensitivity. Staged shares are diagnostic and uncalibrated, so this
result blocks economic interpretation of the staged threshold.

## 9. Reproducibility

The workflow records:

- master seeds and initialization signatures;
- raw paired results;
- refined curves and threshold maps;
- threshold bootstraps;
- budget-rounding diagnostics;
- staged-accounting robustness; and
- SHA-256 hashes.

A second complete reproduction must match the first for every principal
output before final handoff.

## 10. Scientific conclusion

Referrals is not conditionally superior everywhere. Under the primary cost
architecture, it remains competitive across a broad diagnostic cost region in
many social and opportunity-rich conditions, but the advantage disappears
when the exposure chain is sufficiently constrained.

The result is not yet economically calibrated. The model should not add
Consumat logics until empirical activity shares or a defensible theoretical
allocation for staged costs is available, especially for abundant-budget
contexts.
