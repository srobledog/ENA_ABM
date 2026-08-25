# Protocol Correction v0.5

**Recorded:** 2026-07-25  
**Timing:** after the main cost grid completed, before sensitivity,
competitiveness classification, robustness, or substantive interpretation.

## Inconsistency

The frozen design predeclared a comparison at \(r=1.20\), corresponding to the
v0.4 baseline threshold. The configured coarse grid contained 1.00 and 1.25,
but not 1.20. Refinement generated 1.20 only for profiles whose crossing
bracket included that point. Therefore, the registered comparison could not be
computed consistently across all 96 profiles.

## Correction

Execute one additional paired cell at \(r=1.20\) for every registered profile,
using:

- the same model;
- the same experiment seed;
- the same profile-specific initialization namespace;
- 400 paired replications; and
- upfront expected cost accounting.

Store this contrast separately as
`main_fixed_cost_1.20_runs_v0.5.csv.gz` and
`main_fixed_cost_1.20_summary_v0.5.csv`.

## Scope

This correction does not alter the coarse grid, refined crossings, primary
thresholds, bootstrap thresholds, parameter ranges, replication count, or
stopping rules. It completes a comparison already declared in the design and
is not motivated by observed strategy performance.
