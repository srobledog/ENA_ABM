#!/usr/bin/env bash
set -euo pipefail

# Run from the root of the extracted ENA_ABM_v0.5_reproducible package.
PYTHON_BIN="${PYTHON_BIN:-python}"
WORKERS="${WORKERS:-4}"
export PYTHONPATH="src"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/ena_abm_mpl}"
mkdir -p "$MPLCONFIGDIR"

"$PYTHON_BIN" -m unittest discover -s tests -v
"$PYTHON_BIN" scripts/verify_frozen_v0_4.py

"$PYTHON_BIN" scripts/run_main_study_v0_5.py \
  --config configs/main_study_v0.5.json \
  --output outputs/main_study_v0_5/run1 \
  --workers "$WORKERS"

"$PYTHON_BIN" scripts/run_main_study_v0_5.py \
  --config configs/main_study_v0.5.json \
  --output outputs/main_study_v0_5/run2 \
  --workers "$WORKERS"

# Current v0.5 writers already use mtime=0. This step is idempotent and also
# repairs timestamp-bearing gzip files created by an earlier writer.
"$PYTHON_BIN" scripts/canonicalize_gzip_v0_5.py \
  outputs/main_study_v0_5/run1 outputs/main_study_v0_5/run2

# Rebuild per-run hashes after canonicalization without rerunning simulations.
"$PYTHON_BIN" scripts/rebuild_run_manifest_v0_5.py \
  outputs/main_study_v0_5/run1 configs/main_study_v0.5.json
"$PYTHON_BIN" scripts/rebuild_run_manifest_v0_5.py \
  outputs/main_study_v0_5/run2 configs/main_study_v0.5.json

"$PYTHON_BIN" scripts/compare_main_reproductions_v0_5.py \
  outputs/main_study_v0_5/run1 \
  outputs/main_study_v0_5/run2

"$PYTHON_BIN" scripts/check_expected_outputs_v0_5.py \
  outputs/main_study_v0_5/run1 \
  outputs/main_study_v0_5/run2 \
  outputs/main_study_v0_5/reproduction_comparison_v0.5.csv
