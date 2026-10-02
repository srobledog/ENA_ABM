MECHANISM EXPERIMENT v0.1

Base: v0.5.0 commit e45d11f03da12c67c756f00794041ab1fc7d6dff.
The original model, decision, strategies, config and existing tests are unchanged.
MechanismModel inherits the original model. Two explicit methods are copied with
guarded interventions; build_mechanism_methods.py documents their transformations.

From the repository root, with Python 3.11 or later:
  PYTHONPATH=src python -m unittest discover -s tests -q
  PYTHONPATH=src python scripts/verify_mechanisms_v0_1.py --archive-dir FROZEN_RELEASE_FILES --output verification
  PYTHONPATH=src python scripts/run_mechanisms_v0_1.py --output pilot_run1 --workers 4
  PYTHONPATH=src python scripts/run_mechanisms_v0_1.py --output pilot_run2 --workers 4

The published release SHA256 is verified before extracting the two archived files:
main_paired_runs_v0.5.csv.gz and main_fixed_cost_1.20_runs_v0.5.csv.gz.
Original summaries are compared against the archived 240 paired rows. Events and
consumer states are compared against independently rerunning the untouched model
because the published paired CSV does not contain complete event/state traces.

Output folders must not already exist. Every profile is an independent partition
containing deterministic gzip JSONL files. Shared initialization is recorded once
per profile-replication block; each block has 4 direct and 16 referral trajectories.
All actual trajectories are audited before their outputs are written.
Trace files are written to .part files, flushed and fsynced, then atomically
renamed. The parent process rechecks each compressed and logical SHA256 and
reads each gzip to its CRC/end marker before writing the execution manifest.

Compare published files' SHA256, excluding manifest.json and unpublished .part
temporary files. Manifests contain runtime metadata. Use the comparison command:
  python scripts/compare_mechanisms_v0_1.py --first pilot_run1 --second pilot_run2 --output reproduction.json
The analytical benchmark is diagnostic and has no probabilities fitted to outcomes.

The pilot is technical, not a confirmatory study. Do not pool its seed namespace
with the main study. Config main_execution_authorized_by_this_pilot is false.
The simulation executor is ready; the 10000-sample confirmatory bootstrap analysis
must be implemented and verified before executing and interpreting the main study.

Event dictionary additions:
local_candidate_id: local neighbor chosen before the artificial replacement.
target_state_before: awareness/adoption state before processing an exposure.
target_previous_exposures: count of prior exposure events received by this target.
target_degree: fixed undirected consumer-network degree.
target_neighbor_adopted_share: adopted-neighbor fraction at start of current tick.
evaluation_cause: exposure, neighbor_change, or both (active triggering rules).
observed_neighbor_change: change in count since last evaluation; logged even in E.
first_evaluation: no earlier decision evaluation for this consumer.
individual_utility_component and social_utility_component: terms entering utility.

N allows exposure or neighbor-change reevaluation. E permits evaluation only after
an exposure in that tick but retains current social evidence when beta is active.
beta-off does not remove social reliance from the individual term. A keeps all
access gates and the original local-target draw, and draws its artificial target
only after successful introduction. A does not force equal realized exposures.
