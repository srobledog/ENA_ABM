# ENA-ABM

Reproducible agent-based simulation supporting the theoretical study:

> **When Do Referrals Outperform Direct Outreach? An Agent-Based Study of Entrepreneurial Network Activation**

The model compares direct and referral-based customer acquisition under heterogeneous behavioral, relational, structural, and economic conditions. It was implemented as the purpose-built Python package `ena_abm`; it does not use NetLogo, Mesa, or NetworkX.

## Evidence boundary

This repository contains a theoretical computational experiment with diagnostic, not empirically calibrated, parameters. Its results describe the designed parameter space and should not be interpreted as estimates of real-market prevalence or causal effects.

## Main design

The design and results below describe the frozen base study v0.5.0. Current
`main` also includes the subsequent mechanism and signed-social extensions,
integrated from `codex/mechanisms-v0.1-pilot` on 2026-10-07. Despite that branch
name, its history includes the completed main-study implementation and report.
See [integration verification](docs/INTEGRATION_VERIFICATION_2026-10-07.md),
[mechanism instructions](scripts/README_mechanisms.txt), and the
[signed-social results report](docs/SIGNED_SOCIAL_MAIN_RESULTS_v0.1.md).
The original v0.5.0 tag remains unchanged. Integration does not constitute a
public deposit of the extension data or the current manuscript and supplements.

- 96 stratified parameter profiles, balanced across ring, small-world, and preferential-attachment networks.
- 100 consumer nodes in the primary design.
- 30 abstract simulation ticks and two acquisition actions per tick.
- 400 paired replications per cell using shared initialization and matched random streams.
- Relative referral cost `r = C_R / C_D` and profile-specific competitive threshold `r*`.
- Process, accounting, structural, and dynamic robustness checks.
- Two complete independent reproductions.

## Main results

- 91 of 96 profiles yielded finite interpretable thresholds.
- Median `r* = 1.05` (interquartile range 1.00–1.20; finite range 0.85–2.80).
- At equal cost, referrals were competitive in 77.1% of the designed profiles and generated 0.49 additional adoptions on average.
- At `r = 1.20`, referrals were competitive in 26.0% of profiles and generated 0.81 fewer adoptions on average.
- All 64 automated tests passed.
- The 34 principal outputs from the two reproductions are byte-identical after deterministic gzip-header normalization.

## Repository structure

```text
configs/          Frozen configuration for the v0.5 main study
docs/             Model specification, preregistered design, logs, and validation reports
results/          Summary tables, figures, and verification evidence
scripts/          Main-study, validation, comparison, and reproduction scripts
src/ena_abm/      Purpose-built Python simulation package
supplementary/    Appendices S1–S7 and machine-readable companion files
tests/            Automated model and reproducibility tests
```

Large raw paired-run outputs are intentionally excluded from Git history. They are distributed as assets of the [v0.5.0 release](https://github.com/srobledog/ENA_ABM/releases/tag/v0.5.0).

## Installation

Python 3.11 or later is required. The reference environment was verified with Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements_reproduction_v0.5.txt
python -m pip install -e .
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

## Run the automated tests

The verified suite uses Python's standard `unittest` runner:

```bash
python -m unittest discover -s tests -v
```

Expected result: `Ran 64 tests` and `OK`.

## Run the main study

The full main study is computationally intensive and writes large compressed outputs:

```bash
python scripts/run_main_study_v0_5.py \
  --config configs/main_study_v0.5.json \
  --output outputs/main_study_v0_5/run1
```

For the complete two-run workflow, including hash normalization and comparison, see [`supplementary/Appendix_S7_Computational_Environment_and_Reproduction_Workflow.md`](supplementary/Appendix_S7_Computational_Environment_and_Reproduction_Workflow.md) and run:

```bash
bash scripts/run_full_reproduction_v0.5.sh
```

## Reproducibility packages

The release provides:

- `ENA_ABM_v0.5_reproducible.zip`: frozen source, configuration, scripts, tests, and complete verified outputs.
- `ENA_ABM_v0.5_results.zip`: results and reporting package.

SHA-256 checksums:

```text
8d4461fdbb022c5cc20ab82c46a84e005a2d0c6a446ca4ddf71cb9b0ff0394ec  ENA_ABM_v0.5_reproducible.zip
948ae6d1ba87aed06cb82af0cd688c86c2333da8eb7c8433b8331ee9ddd90567  ENA_ABM_v0.5_results.zip
```

## Authors

- Sebastián Robledo Giraldo
- Alexandra Montoya
- Ana Emilia Cordero Borjas

## Funding and acknowledgments

The study received no external funding. It acknowledges Universidad Nacional de Colombia, Sede de La Paz, and project 68790, *Formación investigativa en red: diseño y análisis de un modelo de colaboración entre estudiantes y profesores para la producción de conocimiento*.

## License

The source code is released under the [MIT License](LICENSE). See individual manuscript and supplementary files for their scholarly-use context.
