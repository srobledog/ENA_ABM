# Signed-social robustness extension v0.1

This is a prospective extension motivated by the completed mechanism study,
not a replacement of its model or confirmatory results. Only a technical pilot
is enabled. The primary model and the original mechanism runner are unchanged.

At fixed state let w = beta_social * social_reliance and z = w * (2*s - 1).
Modes are S=z, P=max(z,0), M=min(z,0), Z=0. All other decision components remain
unchanged; S=P+M in utility does not imply additive trajectory outcomes.
P retains the 0.5 threshold and does not represent all positive-influence models.

The technical pilot uses the previously selected 12 profiles, 100 replicates,
four modes, N scheduling, direct outreach plus local/global referrals at costs
1 and 1.2: 20 trajectories per block, 24,000 total. Direct references are shared
across costs. Seed 2026100301 and namespace signed_social_v0.1_pilot are separate
from prior experiments. No efficacy-based scenario selection or stopping.

Run from repository root with Python 3.11+ and project dependencies:

```bash
PYTHONPATH=src python -m unittest discover -s tests -q
PYTHONPATH=src python scripts/run_signed_social_pilot.py --output /absolute/output --workers 2
# After interruption, with identical source/configuration:
PYTHONPATH=src python scripts/run_signed_social_pilot.py --output /absolute/output --workers 2 --resume
```

Each profile has compressed full events, ticks, final states and initializations,
run-level audits, paired contrasts and a verified checkpoint. Partial profiles
are retained in recovery on resume. The runner stops at less than 2 GiB free;
this operational threshold is not a scientific stopping rule. Source hashes in
execution_identity.json bind resumptions to the exact code and specification.

Diagnostics store positive/negative potential utility components even when one
is disabled. `social_utility_component` is the actual active term. In evaluation
events `previous_exposures` counts all exposures received before evaluation,
including the current triggering exposure; exposure events separately retain
the legacy `target_previous_exposures` count before the new exposure.

Validation includes 60 legacy trajectories (P069/P062, three original pilot
replicates, ten S/Z conditions), exact common-event fields, summaries, ticks and
states; pointwise identities; and independent event-level utility, probability,
neighborhood-evidence, access and budget checks on every pilot trajectory.

The full prospective protocol is archived separately and transcribed in
SIGNED_SOCIAL_PROTOCOL_v0.1.txt. Pilot summaries are descriptive, not the
predeclared main-study bootstrap or evidence of empirical validity.
