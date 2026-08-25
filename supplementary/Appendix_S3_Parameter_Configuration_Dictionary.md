# Appendix S3. Parameter and configuration dictionary

## ENA-ABM v0.5 main theoretical experiment

This appendix defines the configuration fields used to generate, execute, and analyze the version 0.5 experiment. It complements Appendix S1, which describes the model using the ODD protocol, and Appendix S2, which records the preregistered experimental design. The values are diagnostic theoretical inputs rather than empirically calibrated estimates.

The appendix distinguishes three configuration layers: (i) model fields accepted by one simulation run; (ii) design fields used to construct the 96 registered profiles and the relative-cost search; and (iii) analysis fields governing replication, bootstrap estimation, robustness variants, and interpretation stop rules. The machine-readable files supplied with this appendix are authoritative for exact execution.

## S3.1 Machine-readable artifact set and precedence

| Artifact | Contents | Use |
|---|---|---|
| `main_study_v0.5.json` | Experiment seed, replication counts, cost grid, main parameter ranges, fixed settings, robustness overrides, and stop-rule values | Primary machine-readable configuration for the v0.5 experiment |
| `registered_profiles_v0.5.csv` | One row for each profile P001–P096, including all nine varied factors and network type | Exact profile registry; use this file instead of regenerating the Latin hypercube |
| `PREREGISTERED_DESIGN_v0.5.md` | Frozen design rationale, estimands, analysis plan, and interpretation rules | Narrative authority for the preregistered design; source for Appendix S2 |
| Version 0.4 source code | Validated ABM implementation, configuration schema, process rules, and output calculations | Executable authority for model behavior; source for Appendix S1 |
| `PROTOCOL_CORRECTION_v0.5.md` | Timing, rationale, and limits of the separately executed fixed-cost comparison at $r=1.20$ | Authority for the documented protocol correction |

If narrative rounding differs from a machine-readable value, the JSON and CSV values take precedence. The profile registry must not be reconstructed from the stated ranges because its deterministic row assignments are part of the frozen design.

## S3.2 Value categories and notation

| Category | Meaning |
|---|---|
| Profile-varying | A value recorded separately for each of the 96 registered profiles |
| Main fixed | A value held constant across the main profile experiment |
| Strategy-specific | A field whose value or use differs between direct and referral runs |
| Derived | A value calculated from one or more stored fields before or after a run |
| Robustness override | A prespecified replacement applied only in a named robustness context |
| Analysis control | A value governing replication, estimation, classification, or stopping rather than agent behavior |

Probabilities and shares are dimensionless and lie in $[0,1]$. Costs are expressed in normalized direct-attempt cost units, ticks are discrete simulation periods, and counts are nonnegative integers unless stated otherwise.

## S3.3 Registered profile fields

The complete values appear in `registered_profiles_v0.5.csv`. Continuous profile factors were assigned by a deterministic stratified Latin-hypercube design. Budget and seed-adopter values were mapped to valid integers. Network type is balanced at 32 profiles per structure.

| Field | Symbol or label | Type / unit | Registered domain | Definition |
|---|---|---|---:|---|
| `profile` | Profile ID | String | P001–P096 | Stable identifier joining design, simulation, and result records |
| `market_sociality` | $\lambda$ | Probability weight | 0.00–1.00 | Market-level tendency for consumer evaluation to rely on social rather than individual information |
| `fit_mean` | $\mu_q$ | Share | 0.35–0.80 | Mean of the truncated-normal product–consumer fit distribution |
| `status_mean` | $\mu_s$ | Share | 0.20–0.80 | Target mean of the initial status-quo satisfaction beta distribution |
| `uncertainty_mean` | $\mu_u$ | Share | 0.20–0.85 | Target mean of the initial uncertainty beta distribution |
| `beta_0` | $\beta_0$ | Logit coefficient | −1.50–0.50 | Intercept in adoption utility |
| `beta_individual` | $\beta_{ind}$ | Logit coefficient | 1.00–6.00 | Weight on individual appeal in adoption utility |
| `beta_social` | $\beta_{soc}$ | Logit coefficient | 0.00–6.00 | Weight on local social information in adoption utility |
| `budget_limit` | $B$ | Direct-cost units | 8–60 | Equal budget allocated separately to each strategy run |
| `seed_adopters` | $n_0$ | Consumers | 1–8 | Consumers initialized as adopters before entrepreneurial actions begin |
| `network_type` | Network structure | Categorical | `ring`, `small_world`, `preferential_attachment` | Rule used to generate the undirected consumer network |

## S3.4 Main fixed model settings

### S3.4.1 Population, network, and schedule

| Field | Type / unit | Main value | Definition |
|---|---|---:|---|
| `n_consumers` | Consumers | 100 | Number of consumer agents in each main-study run |
| `mean_degree` | Edges per consumer | 6 | Target degree for comparable ring and small-world networks and structural scale for preferential attachment |
| `rewire_probability` | Probability | 0.10 | Watts–Strogatz edge-rewiring probability; relevant to the small-world structure |
| `horizon` | Ticks | 30 | Maximum number of simulation ticks |
| `actions_per_tick` | Initiated actions | 2 | Entrepreneurial action capacity per tick, subject to feasibility and remaining budget |
| `allow_repeated_direct_contact` | Boolean | `true` | Allows direct outreach to return to nonadopters after the uncontacted candidate pool is exhausted |

For noncustom generated networks, the implementation requires `n_consumers` to be at least 2 and `mean_degree` to be even, at least 2, and smaller than `n_consumers`.

### S3.4.2 Consumer heterogeneity and information

| Field | Symbol | Type / unit | Main value | Definition |
|---|---|---|---:|---|
| `fit_sd` | $\sigma_q$ | Share | 0.15 | Standard deviation of product fit before truncation to $[0,1]$ |
| `minimum_uncertainty` | $u_{min}$ | Share | 0.05 | Lower bound for uncertainty after information updates |
| `delta_information` | $\delta$ | Share | 0.25 | Magnitude of the uncertainty reduction generated by effective exposure, scaled by source credibility |
| `direct_source_credibility` | $\kappa_D$ | Share | 0.60 | Credibility attached to information arriving through direct outreach |
| `referral_source_credibility` | $\kappa_R$ | Share | 0.60 | Credibility attached to information arriving through referral outreach |

Product fit is sampled from a normal distribution with profile mean `fit_mean` and standard deviation `fit_sd`, then bounded to $[0,1]$. Initial status-quo satisfaction and uncertainty are beta-distributed. For a registered design mean $m$, the profile builder uses concentration 10 and sets

$$
\alpha=10m,\qquad \beta=10(1-m).
\qquad \text{(S3.1)}
$$

Thus the requested mean is preserved while dispersion is held comparable across profiles. Values passed to this mapping are bounded internally to $[0.01,0.99]$; all registered means already lie inside that interval. Seed adopters are selected uniformly without replacement and do not count as new adoptions in the primary outcome.

### S3.4.3 Adoption coefficients and dynamic classifications

| Field | Type / unit | Main value or source | Definition |
|---|---|---:|---|
| `beta_0` | Logit coefficient | Profile-varying | Baseline adoption propensity |
| `beta_individual` | Logit coefficient | Profile-varying | Strength of product fit relative to status-quo satisfaction |
| `beta_social` | Logit coefficient | Profile-varying | Strength of the adopted-neighbor signal |
| `market_sociality` | Share | Profile-varying | Scales reliance on social information as uncertainty changes |
| `takeoff_share` | Share of nonseed market | 0.10 | Threshold used to classify takeoff in the primary analysis |
| `quiet_period` | Ticks | 5 | No-new-adoption window used in the primary extinction definition |

These fields parameterize the common evaluation and adoption mechanism described in Appendix S1. Strategy does not enter the adoption equation directly; it affects which consumers obtain effective exposure and how much budget is consumed in producing it.

## S3.5 Access-process configuration

| Field | Route | Type | Main value | Definition |
|---|---|---|---:|---|
| `direct_exposure_probability` | Direct | Probability | 0.512 | Conditional probability that an initiated direct contact becomes an effective exposure |
| `referral_acceptance_probability` | Referral | Probability | 0.80 | Probability that an available adopted source accepts the request |
| `referral_neighbor_availability_probability` | Referral | Probability | 0.80 | Conditional probability that the accepted source has a locally eligible nonadopter |
| `referral_introduction_probability` | Referral | Probability | 0.80 | Conditional probability that an eligible referral becomes an effective introduction |

The neutral referral pipeline has conditional completion probability

$$
p_R=0.80\times0.80\times0.80=0.512,
\qquad \text{(S3.2)}
$$

which equals the main direct effective-exposure probability. This equality controls the conditional completion probability only. Referral outreach still requires an adopted source and a locally eligible neighbor; direct outreach can select from the wider eligible market. A referral opportunity with no adopted source is recorded as unavailable, does not initiate an attempt, and consumes no budget.

## S3.6 Resource allocation and cost accounting

| Field | Type / unit | Main setting | Definition |
|---|---|---:|---|
| `fairness_criterion` | Categorical | `equal_budget` | Both strategies receive the same profile-specific allocated budget |
| `budget_limit` | Direct-cost units | Profile-varying, 8–60 | Maximum expenditure permitted in one strategy run |
| `direct_action_cost` | Cost units | 1.00 | Normalized expected cost of one initiated direct attempt |
| `referral_action_cost` | Cost units | $r$ | Expected cost of one initiated referral attempt |
| `cost_accounting` | Categorical | `upfront_expected` | Full expected attempt cost is charged when a feasible attempt begins |
| Direct stage shares | Four shares | 0.25 each | Diagnostic search, contact, coordination, and follow-up shares used only under staged accounting |
| Referral stage shares | Four shares | 0.25 each | Diagnostic identification, request, coordination, and follow-up shares used only under staged accounting |

The relative-cost parameter is

$$
r=\frac{C_R}{C_D},\qquad C_D=1,
\qquad \text{(S3.3)}
$$

so $r=1$ means equal attempt cost, $r>1$ means that a referral attempt is more costly, and $r<1$ means that it is less costly. Under `upfront_expected`, failure after initiation remains costly. Under the robustness value `staged`, only stages reached are charged. The 0.25 stage shares are diagnostic accounting assumptions, not observed business cost shares.

The configuration class also contains `action_budget` and `exposure_quota` for alternative comparison criteria. They are not the binding fairness resources in the v0.5 main experiment; `budget_limit` under `equal_budget` is the operative constraint.

## S3.7 Relative-cost search and threshold controls

| Field | Type | Value | Role |
|---|---|---:|---|
| `relative_cost.coarse_grid` | Ordered numeric vector | 0.25, 0.50, …, 3.00 | Initial values of $r$ evaluated for every profile |
| `relative_cost.refinement_tolerance` | Cost-ratio increment | 0.05 | Spacing of intermediate evaluations inside every sign-change bracket |
| `replicates` | Paired replications per cell | 400 | Monte Carlo sample used for each profile–cost comparison |
| `bootstrap_samples` | Paired resamples | 500 | Within-profile resamples used to estimate threshold uncertainty |
| `experiment_seed` | Integer | 2026072505 | Master experiment namespace for deterministic profile execution |

The profile-specific competitive threshold is the largest evaluated $r$ for which the mean paired adoption difference is nonnegative. Profiles without a competitive region and profiles competitive through $r=3.00$ remain absent and right-censored, respectively; the algorithm does not force a finite crossing.

## S3.8 Randomization, pairing, and reproducibility fields

| Field or stream | Scope | Definition |
|---|---|---|
| `experiment_seed` | Complete v0.5 experiment | Reproduces design execution and analysis when combined with the frozen code and artifacts |
| `master_seed` | Simulation namespace | Root value from which stable component seeds are derived for a configured run |
| `replicate_id` | One paired market realization | Identifies a replication within a profile and cost cell |
| `network_seed` | Component stream | Network generation |
| `attribute_seed` | Component stream | Consumer fit, status satisfaction, and uncertainty |
| `seed_selection_seed` | Component stream | Initial adopter selection |
| `strategy_seed` | Component stream | Strategy-level selection operations |
| `exposure_process_seed` | Component stream | Direct exposure and referral-stage outcomes |
| `decision_seed` | Component stream | Adoption draws |

Direct and referral runs within a profile–replication pair share the initialized network, consumer attributes, and seed adopters. Component-specific deterministic streams prevent an unrelated random draw in one process from silently changing another process. Reproduction therefore requires the frozen profile row, replicate identifier, cost ratio, experiment configuration, source code, and seed construction—not merely the headline seed.

## S3.9 Process-robustness override dictionary

Blank entries retain the neutral main-study value. Each regime is evaluated separately for ring, small-world, and preferential-attachment networks.

| Regime key | Direct exposure | Acceptance | Eligible neighbor | Introduction |
|---|---:|---:|---:|---:|
| `neutral` | 0.512 | 0.80 | 0.80 | 0.80 |
| `equal_high` | 0.729 | 0.90 | 0.90 | 0.90 |
| `direct_exposure_advantage` | 0.80 | 0.80 | 0.80 | 0.80 |
| `referral_exposure_advantage` | 0.512 | 0.90 | 0.90 | 0.90 |
| `acceptance_low` | 0.512 | 0.40 | 0.80 | 0.80 |
| `acceptance_high` | 0.512 | 1.00 | 0.80 | 0.80 |
| `eligible_neighbors_none` | 0.512 | 0.80 | 0.00 | 0.80 |
| `eligible_neighbors_abundant` | 0.512 | 0.80 | 1.00 | 0.80 |

The equal-high direct value is $0.729=0.90^3$. The process variants change access probabilities only and do not modify the common evaluation or adoption mechanism.

## S3.10 Accounting-robustness contexts

Each context is run under `upfront_expected` and `staged` accounting while all unlisted values remain at the baseline context setting.

| Context key | Override |
|---|---|
| `baseline` | None |
| `sociality_low` | `market_sociality = 0.10` |
| `sociality_high` | `market_sociality = 0.90` |
| `budget_scarce` | `budget_limit = 8` |
| `budget_abundant` | `budget_limit = 60` |
| `referrers_scarce` | `seed_adopters = 1` |
| `referrers_abundant` | `seed_adopters = 8` |
| `network_ring` | `network_type = ring` |
| `network_preferential_attachment` | `network_type = preferential_attachment` |

## S3.11 Structural-robustness contexts

| Context key | Override |
|---|---|
| `baseline` | None |
| `network_size_small` | `n_consumers = 50` |
| `network_size_large` | `n_consumers = 200` |
| `mean_degree_low` | `mean_degree = 4` |
| `mean_degree_high` | `mean_degree = 10` |
| `rewiring_zero` | `rewire_probability = 0.00` |
| `rewiring_high` | `rewire_probability = 0.30` |
| `network_ring` | `network_type = ring` |
| `network_preferential_attachment` | `network_type = preferential_attachment` |

These contexts alter existing structural parameters only; they do not introduce new agents, decision rules, or diffusion mechanisms.

## S3.12 Dynamic-definition robustness

| Field | Values | Effect |
|---|---|---|
| `relative_cost_values` | 1.00, 1.20 | Cost settings at which alternative dynamic classifications are summarized |
| `takeoff_shares` | 0.05, 0.10, 0.15, 0.20 | Alternative shares of the nonseed market used to classify takeoff |
| `quiet_periods` | 3, 5, 10 ticks | Alternative no-new-adoption windows used to classify extinction |

These alternatives recalculate classifications from simulated histories; they do not change exposure, evaluation, or adoption events.

## S3.13 Analysis stop-rule configuration

| JSON field | Value | Operational meaning |
|---|---:|---|
| `multiple_crossing_share_max` | 0.10 | Maximum tolerated share of main profiles with multiple competitive-region crossings before stopping substantive threshold interpretation |
| `unstable_bootstrap_interval_width_max` | 0.50 | Width used to flag unstable profile-level bootstrap threshold intervals |
| `accounting_difference_material` | 0.25 | Cost-ratio difference treated as materially important in the accounting comparison |
| `budget_rounding_share_material` | 0.10 | Share used to flag material budget-residual or rounding influence |
| `minimum_interpretable_profile_share` | 0.50 | Minimum share of profiles required to yield interpretable competitive regions |
| `reproducibility_required` | `true` | Requires an independent complete reproduction before accepting the analysis package |

These fields are interpretation controls. They do not remove scientifically valid low-adoption, zero-adoption, unavailable-opportunity, extinction, absent-region, or right-censored runs.

## S3.14 Derived quantities and outcome fields

| Quantity or outcome | Definition |
|---|---|
| New adopters | Final adopters minus initial seed adopters; primary strategy outcome |
| Paired adoption difference | Referral new adopters minus direct new adopters for the same profile and replication |
| $r^*$ | Largest evaluated relative cost with a nonnegative mean paired adoption difference, subject to profile classification |
| Unavailable referral opportunity | Scheduled referral action for which no adopted source is available; no attempt and no cost |
| Referral request accepted | Initiated referral attempt that passes the acceptance stage |
| Eligible neighbor | Accepted source with a locally eligible nonadopter after the availability process |
| Effective introduction | Eligible referral that completes the introduction stage and creates exposure |
| Effective direct exposure | Initiated direct attempt that passes its exposure process |
| Conversion after exposure | New adoption divided by effective exposures, reported separately from access generation |
| Budget remaining | Allocated budget minus charged strategy cost at termination |
| Takeoff | New adoption reaches the configured share of the nonseed population |
| Extinction | No takeoff, entrepreneurial action has ended, and no new adoption occurs during the configured quiet period |
| Cascade depth and reach | Referral-parent-based measures of how far adoption descendants extend from seed adopters |

## S3.15 Validation domains and implementation safeguards

The configuration validator requires probabilities and shares to remain in $[0,1]$; positive action costs; nonnegative resource limits; at least one action per tick; a positive horizon and quiet period; positive beta-distribution shape parameters; valid strategy, network, fairness, and accounting labels; and direct and referral stage shares that each sum to one. The seed-adopter count must be nonnegative and smaller than the population.

Every run records a configuration and initialization signature. Paired strategy runs must have identical initialization signatures. Invalid probabilities, impossible resource settings, unknown fields, mismatched initialization, or malformed networks raise errors rather than being silently repaired during execution.

## S3.16 Reproduction note and interpretation boundary

To reproduce the main experiment, use the frozen version 0.4 model implementation together with `main_study_v0.5.json` and the supplied `registered_profiles_v0.5.csv`. Do not sample new profile values from the reported ranges. The separately documented $r=1.20$ comparison completes a preregistered contrast but does not change the primary grid or threshold estimates.

The parameter dictionary defines a theoretical design space. Values such as 0.80 acceptance, 0.60 credibility, or the 8–60 budget range are controlled experimental inputs. They must not be interpreted as measured market averages, estimated causal effects, or recommended managerial constants. Empirical calibration and external validation are required before translating a simulated threshold into a firm-specific decision rule.
