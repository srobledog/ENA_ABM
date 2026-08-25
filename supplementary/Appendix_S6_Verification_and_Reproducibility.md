# Appendix S6. Verification and reproducibility

## ENA-ABM v0.5 main theoretical experiment

This appendix documents the integrity checks, automated verification, interpretation stop gates, protocol correction, and independent complete reproduction of the version 0.5 experiment. Appendix S7 provides the executable reproduction instructions. Verification establishes that the frozen computational study can be regenerated consistently; it does not provide empirical calibration or external validation.

## S6.1 Verification summary

### Table S6.1. Verification status of the frozen experiment

| Verification layer | Observed result | Status |
|---|---|---|
| Automated tests | 64/64 passed | Pass |
| Frozen v0.4 source files | 15/15 SHA-256 matches | Pass |
| Run 1 paired rows | 972,800 | Pass |
| Run 2 paired rows | 972,800 | Pass |
| Principal outputs | 34/34 byte-identical after canonical gzip headers | Pass |
| Initially timestamp-sensitive gzip files | 7/7 decompressed logical hashes matched | Pass |
| Interpretation stop gate | No blocker activated | Pass |
| Empirical calibration | Not performed; parameters are diagnostic | Boundary |

The verification chain distinguishes four questions: whether the inherited model source changed, whether automated behavioral and design tests passed, whether the planned interpretation gates remained open, and whether a second execution regenerated the same scientific artifacts.

## S6.2 Frozen architecture and automated tests

The version 0.5 study used the validated version 0.4 behavioral architecture without modification. SHA-256 comparison against the registered v0.4 checkpoint confirmed that all 15 files under `src/ena_abm/` were unchanged. The test suite combined 59 inherited model tests with five v0.5 design tests. All 64 tests passed with zero failures and zero errors.

### Table S6.2. Registered source-file integrity check

| Frozen source file | SHA-256 prefix | v0.5 comparison |
|---|---|---|
| src/ena\_abm/\_\_init\_\_.py | 6ac16adbf8ed42f9… | Match |
| src/ena\_abm/\_\_main\_\_.py | 6d8b7d7846a84505… | Match |
| src/ena\_abm/agents.py | cc0a5561893dc1e8… | Match |
| src/ena\_abm/analysis.py | 336189aa4c3acb9f… | Match |
| src/ena\_abm/break\_even.py | 1d41d0b7dd0b53a8… | Match |
| src/ena\_abm/cli.py | a4c67eb5cee453a2… | Match |
| src/ena\_abm/config.py | 50b6febf1a0a7b31… | Match |
| src/ena\_abm/decision.py | 721ea4c7497f2b93… | Match |
| src/ena\_abm/events.py | c060f403aab442e2… | Match |
| src/ena\_abm/experiments.py | b1b5abf04297be87… | Match |
| src/ena\_abm/model.py | bfc3a65f210f1861… | Match |
| src/ena\_abm/network.py | 86dd02599b11be73… | Match |
| src/ena\_abm/rng.py | 7ca1ba1527e58d24… | Match |
| src/ena\_abm/strategies.py | 90a037a0622ba735… | Match |
| src/ena\_abm/validation.py | 490e584b36b2f9e1… | Match |

*Note.* Prefixes are shown for readability. `Table_S6_2_Frozen_Source_Hash_Check.csv` and the supplied final-hash registries retain the complete 64-character SHA-256 values. Matching source hashes verify implementation identity; they do not by themselves verify that a design or interpretation is appropriate.

## S6.3 Interpretation stop gates

### Table S6.3. Prespecified stopping diagnostics

| Diagnostic | Observed | Decision criterion | Blocker activated |
|---|---|---|---|
| Multiple-crossing share | 0.0% | <= 0.10 | No |
| Finite interpretable share | 94.8% | >= 0.50 | No |
| Bootstrap width > 0.50 share | 3.2% | not widespread | No |
| Rounding residual over limit share | 13.7% | must also dominate threshold ordering | No |
| Material accounting contexts | 1/9 (11.1%) | must reverse central conclusion | No |

No interpretation blocker was activated. The budget-residual diagnostic deserves clarification: 13.7% of all evaluated cells exceeded the residual-share screening limit, but the preregistered stopping condition required both a material residual share and evidence that rounding determined threshold ordering. The second condition was false, so budget rounding did not block interpretation. Similarly, one of nine accounting contexts reached the material difference of 0.25, but the convention did not reverse the central conclusion.

The final machine-readable manifest records `interpretation_blocked: false`, `parameters_empirically_calibrated: false`, 34 principal files, and 972,800 paired rows per execution.

## S6.4 Documented protocol correction

The frozen design declared a fixed comparison at $r=1.20$, but the coarse 0.25-spaced grid contained 1.00 and 1.25 rather than 1.20. Local crossing refinement generated 1.20 only for some profiles. The inconsistency was identified after completion of the main grid and before sensitivity analysis, competitiveness classification, robustness analysis, or substantive interpretation.

The correction executed one additional $r=1.20$ paired cell for every registered profile using the unchanged model, experiment seed, profile-specific initialization namespace, 400 paired replications, and upfront expected-cost accounting. Results were stored separately. The correction did not alter the coarse grid, crossing refinement, primary or bootstrap thresholds, parameter ranges, replication count, stopping rules, or profile selection. It completed a predeclared contrast and was not selected in response to strategy performance.

## S6.5 Independent complete reproduction

The workflow was executed twice from separate output directories without reusing scientific result rows, summaries, bootstrap estimates, robustness tables, figures, or reports. Both executions used the same frozen design and deterministic seed specification, as required for exact computational reproduction. Each produced 972,800 paired result rows.

### Table S6.4. Principal artifacts compared across reproductions

| Artifact class | Files | Byte-identical | Logically identical |
|---|---|---|---|
| Compressed raw-data tables | 7 | 7 | 7 |
| Uncompressed result tables | 16 | 16 | 16 |
| JSON manifests and diagnostics | 4 | 4 | 4 |
| Markdown reports and rules | 3 | 3 | 3 |
| Figures | 4 | 4 | 4 |
| Total | 34 | 34 | 34 |

The 34 principal artifacts consist of 16 uncompressed tables, seven compressed raw-data tables, four figures, four JSON manifests or diagnostics, and three Markdown reports or rule files. The final comparison reports identity for every artifact.

## S6.6 Gzip timestamp normalization

Seven `.csv.gz` files initially had different binary SHA-256 values even though their decompressed CSV contents were identical:

- `accounting_staged_runs_v0.5.csv.gz`
- `accounting_upfront_runs_v0.5.csv.gz`
- `dynamic_robustness_runs_v0.5.csv.gz`
- `main_fixed_cost_1.20_runs_v0.5.csv.gz`
- `main_paired_runs_v0.5.csv.gz`
- `process_robustness_runs_v0.5.csv.gz`
- `structural_robustness_runs_v0.5.csv.gz`

The difference came from gzip header creation times, which are packaging metadata rather than scientific data. The workflow therefore rewrote those files with `mtime=0` while preserving the decompressed CSV bytes, then rebuilt the manifests. After this canonicalization, all seven compressed files and all 34 principal outputs were byte-identical. The logical hashes in `reproduction_comparison_v0.5.csv` preserve the distinction between decompressed scientific identity and container-byte identity.

## S6.7 Manifest and hash architecture

Each run contains two complementary integrity layers:

1. `manifest_v0.5.json` records scientific status, calibration status, configuration and preregistration hashes, paired-row count, interpretation status, and the number of principal artifacts.
2. `principal_hashes_v0.5.csv` records the filename, byte count, and SHA-256 digest of each principal output.

The package-level `final_hashes_v0.5.csv` extends verification to configuration, documentation, source code, scripts, tests, and outputs. The v0.4 hash registry is retained separately so the frozen model-source comparison can be audited without relying on a narrative assertion.

## S6.8 Interpretation boundary and evidence package

The verification establishes that the registered v0.4 implementation was unchanged; all automated checks passed; the complete analysis was regenerated from a clean output location; all principal scientific contents matched; and packaging timestamps were isolated and normalized transparently. It does not establish that the diagnostic parameters represent observed firms, that simulated effects generalize to a population, or that the mechanism has been empirically validated.

The accompanying package contains the complete comparison, manifests, hashes, tests, diagnostics, correction, decision log, and validation report. Appendix S7 provides the executable reproduction workflow.
