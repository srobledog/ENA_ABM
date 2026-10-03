# Signed-social main study: completed

96 fixed profiles, 400 replicates, 20 conditions: 768,000 audited trajectories.
All 96 full-trace archives have persistent backup acknowledgments. Pilot
observations were not pooled. Experiment seed 2026100301, namespace
signed_social_v0.1_main, bootstrap seed 2026100302.

## Registered primary results

10,000 complete-block resamples within profiles; profiles fixed and equally
weighted. Bonferroni 99.375% intervals over eight primary comparisons.

| Cost | Contrast | Mean new adopters | Adjusted interval |
|---|---|---:|---|
| 1.0 | GP | -0.28659 | [-0.32543, -0.24839] |
| 1.0 | BP | 0.05755 | [0.05177, 0.06354] |
| 1.0 | BM | 0.81471 | [0.78711, 0.84137] |
| 1.0 | BM-BP | 0.75716 | [0.72907, 0.78484] |
| 1.2 | GP | -1.71427 | [-1.75189, -1.67811] |
| 1.2 | BP | 0.03891 | [0.03437, 0.04352] |
| 1.2 | BM | 0.93987 | [0.91374, 0.96483] |
| 1.2 | BM-BP | 0.90096 | [0.87478, 0.92606] |

G is local referrals minus direct outreach. P retains positive utility only,
M negative utility only, Z zero; BP=GP-GZ and BM=GM-GZ. BP is detectable but
inside the predefined +/-0.5 diagnostic margin. BM and BM-BP exceed it.

Secondary means GS/GP/GM/GZ are 0.51198/-0.28659/0.47057/-0.34414 at cost 1,
and -0.78609/-1.71427/-0.81331/-1.75318 at cost 1.2. H is -0.01615/-0.01169;
component effects are not exactly additive. Positive-only P retains the 50%
neighbor-adoption threshold. Its small effect does not refute positive social
influence generally. Results concern acquisition under budget, not profit.

The checks independently reconcile all raw gaps and compare primary bootstrap
variances with sum(profile population variances)/400/96^2. They passed.
Monte Carlo intervals are conditional on this theoretical model/design.

## Operational recovery

Initial synchronized-workspace writes produced incomplete/transient files.
Invalid profiles were preserved and rerun with identical seeds. Main execution
was revised to generate and verify in isolated temporary directories before
copying finalized files. Scientific source/configuration identity was checked
before adopting valid earlier profiles. No efficacy-based exclusions occurred.
95 tests passed; separate isolated-transfer validation covered 40 trajectories.

Scripts: run_signed_social_main.py, analyze_signed_social_main.py,
verify_signed_social_analysis.py. Persistent data package retains the identities,
recovery record, raw backup index, paired contrasts and bootstrap distribution.
