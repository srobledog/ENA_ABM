# Main execution plan - signed social v0.1

Pilot gate passed: 24,000 complete trajectories and 94 unit tests, including
60 exact legacy-trajectory comparisons. Main execution adds a tested backup
and interruption-recovery lifecycle. The scientific design remains fixed at
96 profiles x 400 replicates x 20 trajectories = 768,000 trajectories.

Use `configs/signed_social_v0.1_main.json`; namespace `signed_social_v0.1_main`
and seed 2026100301. Pilot replicates are not pooled into the main study.
The eight primary tests are GP, BP, BM, D_components at each of costs 1 and 1.2;
10,000 paired within-profile bootstrap draws, equal fixed-profile weights,
99.375% Bonferroni intervals and diagnostic margin +/-0.5 new adopters.

The implementation executes at most six profiles concurrently and archives
the entire block before admitting the next block. Each profile preserves full
events, ticks, initialization, final states, runs, contrasts and a checkpoint
in a ZIP archive. Compressed/logical hashes and archive bytes are verified
before upload. Every successful receipt is persisted before local eviction.
Runs, paired contrasts, checkpoints and receipts remain locally available.

Only acknowledged backed-up heavy local streams and temporary archive copies
are evicted. No previous study or pilot data are removed. A failed or uncertain
upload retains originals and blocks retry pending receipt reconciliation.
Partial simulation profiles are preserved under recovery and rerun with the
same seeds. Exact source/configuration identity is required for resume.

```bash
PYTHONPATH=src python scripts/run_signed_social_main.py \
  --output /absolute/main-output \
  --upload-helper /absolute/current/library_upload.py --workers 6 --block-size 6
# Add --resume only after an interruption; never change the source identity.
```

The external upload helper is the current authorized persistent-file helper,
not a bundled dependency or a GitHub upload of research traces. Archives are
identified by returned persistent file IDs in the final main manifest.
Resource estimates from the pilot are approximate; worker and block counts
are operational choices and do not alter sample size or inferential weights.
