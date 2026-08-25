# Cost and Exposure Test Catalog v0.4

Expected outcomes were defined before execution.

| Controlled case | Expected result | Observed |
|---|---|---|
| \(r=1\), equivalent mechanisms | Same attempt, exposure, adoption, and cost behavior | Pass |
| \(r<1\) and \(r>1\) | Cost changes without process-probability changes | Pass |
| Exactly divisible budget | Zero residual and exact affordable attempts | Pass |
| Nondivisible budget | Positive residual recorded | Pass |
| Budget below action cost | No attempt and no cost | Pass |
| Failed direct contact | Paid attempt, no exposure | Pass |
| Rejected referral request | Paid attempt, no exposure | Pass |
| Referrer without neighbor | Paid failed attempt | Pass |
| No adopted referrer | Unavailable opportunity, no attempt or cost | Pass |
| Exposure without adoption | Exposure and evaluation, no adoption | Pass |
| Budget conservation | Cost events and balance reconcile | Pass |
| Process separation | Attempt, exposure, evaluation, and adoption are distinct | Pass |
| Probability bounds | Values outside [0,1] rejected | Pass |
| Stage-share bounds | Each strategy's shares sum to one | Pass |
| Staged rejection | Only reached activities charged | Pass |
| Sufficient budget | Accounting conventions preserve behavior | Pass |
| One attempt | At most one effective exposure | Pass |
| Cost-only change | Utility and adoption probability unchanged | Pass |
| Fixed seed | Summary, ticks, and events reproduce | Pass |
| Mean-to-beta mapping | Requested means produce valid shape parameters | Pass |
| Primary threshold | Supremum definition applied | Pass |
| Conservative threshold | Lower confidence limit applied | Pass |
| Refinement | Crossing bracket filled at 0.05 | Pass |
| Multiple crossings | No forced single \(r^*\) | Pass |

The inherited network, simultaneous-update, decision-rule, pairing, budget,
and deterministic-reproduction tests also pass.

**Total:** 59 tests passed.
