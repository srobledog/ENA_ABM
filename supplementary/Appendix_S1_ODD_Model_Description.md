# Appendix S1. ODD model description

## Entrepreneurial customer-acquisition agent-based model

This appendix documents the agent-based model (ABM) used in the article following the Overview, Design concepts, and Details (ODD) protocol (Grimm et al., 2020). It describes the frozen model implemented in version 0.4 and used without changes to the scientific source files in the version 0.5 theoretical experiment. The model compares direct outreach and one-to-one referral outreach under a common post-exposure evaluation and adoption mechanism. All parameter values are diagnostic inputs for theoretical experimentation; they are not empirically calibrated estimates.

## S1.1 Overview

### S1.1.1 Purpose and intended patterns

The model asks when referral-based customer acquisition remains competitive with direct outreach under a fixed entrepreneurial resource constraint. For a parameter profile $\mathbf{x}$, direct-attempt cost $C_D$, referral-attempt cost $C_R$, and cost ratio $r=C_R/C_D$, the primary comparison is the expected difference in new adopters:

$$
\Delta(r\mid\mathbf{x})=\mathbb{E}[Y_R(r,\mathbf{x})-Y_D(\mathbf{x})]
\qquad \text{(S1.1)}
$$

where $Y_R$ and $Y_D$ exclude exogenous seed adopters. The profile-specific competitive threshold is

$$
r^*(\mathbf{x})=\sup\{r:\Delta(r\mid\mathbf{x})\ge 0\}
\qquad \text{(S1.2)}
$$

The intended model-level patterns are: (a) referral competitiveness generally decreases as referral attempts become more expensive relative to direct attempts; (b) referral competitiveness increases when social information is consequential and referral opportunities can be activated; and (c) the competitive region narrows or disappears when request acceptance, eligible-neighbor availability, or effective introduction is weak. These are theoretical patterns generated within the model, not empirical regularities used for calibration.

### S1.1.2 Entities, state variables, and scales

The model contains one entrepreneur, $n$ consumers, and a fixed undirected consumer network. The entrepreneur is represented by global resource and strategy variables rather than by a spatially located node.

| Entity or level | State variables and attributes | Role |
|---|---|---|
| Entrepreneur | strategy; initial and remaining budget; maximum actions per tick; action and exposure counters; cost-accounting convention | Initiates direct or referral attempts subject to resource feasibility. One strategy is used for an entire run. |
| Consumer $i$ | identifier; state; product fit $q_i$; status-quo satisfaction $s_i$; current and initial uncertainty $u_{i,t}$; seed indicator; awareness, evaluation, and adoption times; prior adopted-neighbor count; acquisition source; referral parent; cascade depth | Receives exposure, evaluates the offer, may adopt, and—after adoption—may become a referral source in a later tick. |
| Network | adjacency sets; network type; mean degree; rewiring probability | Determines consumer neighborhoods, structural referral opportunities, and local social information. |
| Run/global state | tick; horizon; random-stream seeds; process counts; outcome measures; initialization signature | Coordinates scheduling, observation, and reproducibility. |

Consumers occupy one of four discrete states: **unaware**, **aware**, **evaluating**, or **adopted**. The model advances in discrete ticks. The main experiment uses 100 consumers, 30 ticks, and at most two entrepreneurial actions per tick. Network and parameter variants are described in Appendices S2 and S3.

The core diagnostic ranges used in the main experiment are summarized below. A complete machine-readable parameter dictionary should accompany Appendix S3.

| Component | Symbol or setting | Main-study specification |
|---|---:|---|
| Market size | $n$ | 100 consumers |
| Network type | — | Ring lattice, Watts–Strogatz small world, preferential attachment |
| Mean degree / rewiring | — | 6 / 0.10 in the main design |
| Horizon / actions per tick | — | 30 / 2 |
| Seed adopters | — | 1–8 |
| Market sociality | $\lambda$ | 0–1 |
| Mean product fit | — | 0.35–0.80; SD 0.15 |
| Mean status threshold | — | 0.20–0.80 |
| Initial uncertainty | $u_{i,0}$ | 0.20–0.85 |
| Adoption intercept | $\beta_0$ | −1.50–0.50 |
| Individual-fit weight | $\beta_{ind}$ | 1–6 |
| Social-influence weight | $\beta_{soc}$ | 0–6 |
| Budget | $B$ | 8–60 direct-cost units |
| Direct effective exposure | — | 0.512 |
| Referral acceptance / neighbor availability / effective introduction | — | 0.80 / 0.80 / 0.80 |
| Information update / minimum uncertainty | $\delta_{info},u_{min}$ | 0.25 / 0.05 |
| Exposure credibility | $c_e$ | 0.60 for both strategies |
| Referral cost ratio | $r=C_R/C_D$ | 0.25–3.00, with local refinement |

### S1.1.3 Process overview and scheduling

Initialization occurs once at $t=0$. The network, consumer attributes, and seed adopters are held fixed within a run. Each subsequent tick uses the following sequence:

1. Store a snapshot of adoption states from the beginning of the tick and calculate each consumer’s adopted-neighbor count from that snapshot.
2. Determine the number of action slots allowed by the per-tick capacity and the remaining resource constraint.
3. Select feasible direct targets or adopted referral sources according to the run’s strategy.
4. Process each initiated attempt in sequence, including its cost and access-stage outcomes. A target can receive at most one entrepreneurial exposure during a tick.
5. Apply successful exposure events: move newly reached consumers to awareness/evaluation and update their uncertainty.
6. Identify aware nonadopters who must evaluate because they were newly exposed or because their adopted-neighbor count changed since their previous evaluation.
7. Calculate adoption probabilities for all triggered consumers using the same decision rule for both acquisition strategies.
8. Draw adoption outcomes and apply state changes simultaneously.
9. Record tick-level and event-level measures, including attempts, failures, exposures, evaluations, adoptions, costs, and remaining budget.

Consumers who adopt during tick $t$ cannot serve as referral sources until a later tick. This snapshot-and-simultaneous-update rule prevents within-tick referral cascades. A run continues through the fixed horizon; once resources or feasible opportunities are exhausted, later ticks produce no new entrepreneurial attempts unless feasibility changes through adoption dynamics.

## S1.2 Design concepts

### S1.2.1 Basic principles

The model separates **access generation** from **post-exposure conversion**. Direct outreach provides broad target access through a short contact process. Referral outreach requires an adopted source and three conditional stages—request acceptance, eligible-neighbor availability, and effective introduction—before exposure occurs. After exposure, both routes use the same uncertainty update and adoption rule. This design prevents referral performance from being driven by an assumed route-specific conversion coefficient.

The model also treats networks as stocks of potential opportunities that must be activated. An adopted contact is a potential source, but a usable customer-acquisition opportunity exists only if the source cooperates, an eligible neighbor is available, and the introduction is completed.

### S1.2.2 Emergence

New adoption, referral cascades, takeoff, extinction, and the cost threshold $r^*$ emerge from the interaction of network structure, initial seed locations, consumer heterogeneity, local adoption states, stochastic access stages, budget depletion, and probabilistic adoption. No target value for these outcomes is imposed.

### S1.2.3 Adaptation, objectives, and decision making

The entrepreneur follows a prespecified strategy rather than optimizing dynamically within a run. The strategy’s action set adapts mechanically to the current state: direct outreach selects eligible nonadopters, whereas referral outreach selects currently adopted sources. Consumers do not optimize intertemporally. When triggered, they adopt probabilistically according to current product fit, status-quo satisfaction, uncertainty, and local adoption evidence.

### S1.2.4 Learning and prediction

The entrepreneur and consumers do not estimate unknown parameters, forecast future states, or learn a policy. Consumer uncertainty can decrease after an exposure, but this is an information update rather than statistical learning. The network remains fixed.

### S1.2.5 Sensing

The entrepreneur observes remaining resources and the eligibility required by the selected strategy. Direct outreach can identify nonadopters without requiring a network tie. Referral outreach can identify adopted sources; acceptance and the availability of an eligible neighbor are then realized during the attempt. Consumers respond to their own attributes, exposure history, and the proportion of neighbors adopted at the beginning of the tick.

### S1.2.6 Interaction

Direct interaction occurs between the entrepreneur and a selected consumer. Referral interaction follows entrepreneur → adopted source → eligible neighbor. Consumer-to-consumer influence enters through observed neighboring adoption states. There is no negative word of mouth, strategic persuasion between consumers, or dynamic rewiring.

### S1.2.7 Stochasticity

Stochastic elements include network generation for small-world and preferential-attachment structures; consumer attributes; seed selection; target or source ordering; direct effective exposure; referral acceptance, neighbor availability, and introduction; and adoption. Separate deterministic random streams are derived from the master seed for network generation, attributes, seed selection, strategy events, exposure-stage outcomes, and adoption. Paired strategy comparisons align the relevant streams and initialization.

### S1.2.8 Collectives

No formal organizations or groups act as agents. Network neighborhoods and referral cascades are observed collectives that arise from consumer ties and acquisition histories.

### S1.2.9 Observation

The primary outcome is the number of new adopters excluding seeds. The model separately records eligible sources, unavailable opportunities, attempts, failed attempts, accepted requests, eligible neighbors, successful introductions, effective exposures, evaluations, and adoptions. It also records cost spent, unused budget, cost per attempt, cost per exposure, cost per new adopter, exposures per attempt, adoption per exposure, time to first adoption, takeoff, extinction, cascade reach, largest referral cascade, and maximum cascade depth. Event records preserve stage-specific outcomes and costs.

## S1.3 Details

### S1.3.1 Initialization

For each replication, initialization proceeds as follows:

1. Derive separate stream seeds from the master seed, network type, replication identifier, and stream label.
2. Generate one undirected network of $n$ consumers. The ring lattice connects each node symmetrically to nearby nodes. The small-world network begins from the ring lattice and rewires eligible edges with the configured probability. The preferential-attachment network adds new nodes using degree-weighted sampling.
3. Draw consumer product fit from a normal distribution truncated to $[0,1]$, using the configured mean and standard deviation.
4. Draw status-quo satisfaction and initial uncertainty from beta distributions whose shape parameters are specified in the run configuration.
5. Select seed adopters uniformly without replacement. Seeds begin in the adopted state at $t=0$, have awareness and adoption time zero, and are excluded from the primary outcome.
6. Set all nonseed consumers to unaware. Initialize the entrepreneur’s budget, strategy, action capacity, accounting convention, and all process counters.
7. Calculate a SHA-256 initialization signature from the network edges, consumer attributes, and seed indicators. This signature supports paired comparisons and reproduction checks.

The main experiment pairs direct and referral runs on network, attributes, seeds, and relevant random streams so that the estimated difference is within replication rather than between unrelated simulated markets.

### S1.3.2 Input data

The model uses **no external empirical input data**. Networks, consumer attributes, seeds, and events are generated internally from the configuration and pseudorandom seeds. The 96 main-study profiles are deterministic design points, not observations sampled from a population. Accordingly, model outputs characterize the specified theoretical design space and must not be interpreted as estimates of real-market frequencies or causal effects.

### S1.3.3 Submodels

#### Network generation

Three fixed undirected network structures are available: ring lattice, Watts–Strogatz small world, and preferential attachment. Self-loops and asymmetric edges are prohibited. Network diagnostics include node and edge counts, average degree, density, average local clustering, number of connected components, and largest-component size.

#### Direct-outreach target selection and exposure

Direct outreach selects nonadopters, prioritizing uncontacted unaware consumers and then other uncontacted nonadopters. If the candidate list is empty and repeated contact is allowed, nonadopters may be selected again. A feasible initiated attempt is charged and produces effective exposure with probability $p_D$. Failure to produce exposure remains a paid attempt. The target does not need to be adjacent to an adopter.

#### Referral source selection and exposure

Referral outreach selects from consumers already adopted at the start of the tick. If no adopted source is available, no attempt begins and no cost is charged. After an attempt begins, the model evaluates:

1. request acceptance with probability $p_A$;
2. structural existence of a nonadopted neighbor not already selected for exposure in that tick;
3. eligible-neighbor availability with probability $p_N$; and
4. effective introduction with probability $p_I$.

Failure after initiation consumes cost under the primary accounting convention. A completed introduction produces one exposure. In the neutral baseline, $p_A=p_N=p_I=0.80$, so the conditional product equals $0.512$, the direct effective-exposure probability. Structural access nevertheless remains strategy-specific.

#### Uncertainty update

An exposure with credibility $c_e$ updates consumer uncertainty as

$$
u^+_{i,t}=\max\{u_{min},u_{i,t}(1-\delta_{info}c_e)\}
\qquad \text{(S1.3)}
$$

Credibility equals 0.60 for both routes in the main study. Thus, route labels do not enter the downstream response mechanism.

#### Social information and adoption

Let $\phi_{i,t}$ be the proportion of consumer $i$’s neighbors adopted at the beginning of tick $t$, with $\phi_{i,t}=0$ for an isolated node. Reliance on social information is

$$
\rho_{i,t}=\lambda u^+_{i,t}
\qquad \text{(S1.4)}
$$

where $\lambda\in[0,1]$ is market sociality. Individual appeal is $I_i=q_i-s_i$. Adoption utility is

$$
U_{i,t}=\beta_0+\beta_{ind}(1-\rho_{i,t})I_i+\beta_{soc}\rho_{i,t}(2\phi_{i,t}-1)
\qquad \text{(S1.5)}
$$

and the adoption probability is

$$
\Pr(A_{i,t}=1)=\frac{1}{1+\exp(-U_{i,t})}
\qquad \text{(S1.6)}
$$

Evaluation is triggered by a new exposure or by a change in the adopted-neighbor count since the consumer’s previous evaluation. Adoption draws are made after all triggered probabilities have been calculated, and successful state changes are applied simultaneously.

#### Cost accounting and resource feasibility

For strategy $s$, expected attempt cost is

$$
C_s=V_TT_s+M_s
\qquad \text{(S1.7)}
$$

where $V_T$ is the value of entrepreneurial time, $T_s$ is expected time per initiated attempt, and $M_s$ is monetary expenditure. Costs are normalized to $C_D=1$ and $C_R=r$. The cost ratio changes only resource consumption; it does not alter acceptance, credibility, exposure, utility, or adoption probabilities.

Under the primary convention, the full expected cost is charged when a feasible attempt begins. No attempt begins if its start cost exceeds the remaining budget. Failure after initiation remains costly, while the absence of a feasible referral source is recorded as an unavailable opportunity and consumes no cost. A staged-accounting variant charges only the activities reached; it is used solely as a robustness check.

#### Dynamic and cascade measures

Takeoff is reached when nonseed adoption equals or exceeds the configured share of the nonseed population (10% in the primary analysis). Extinction requires no takeoff, an end to entrepreneurial action, and no new adoption during the configured quiet window (five ticks in the primary analysis). Referral parent links define cascade depth and descendant counts. Alternative takeoff and extinction definitions are robustness analyses, not changes to consumer behavior.

## S1.4 Scope boundaries and implementation

The model includes only direct outreach and one-to-one referral activation. It excludes negative word of mouth, campaigns, events, presentations, strategic follow-up, incentives as a behavioral mechanism, multiple referrals per action, competition, dynamic networks, changing preferences, heterogeneous credibility in the main experiment, and empirically calibrated parameters.

The frozen implementation is written in Python. The version 0.5 study retained the version 0.4 scientific source files unchanged and added the preregistered experiment, threshold estimation, sensitivity analysis, robustness analyses, and complete independent reproductions. The reproducible package, machine-readable configuration, profile registry, and checksums should be deposited with the article.

## Reference

Grimm, V., Railsback, S. F., Vincenot, C. E., Berger, U., Gallagher, C., DeAngelis, D. L., et al. (2020). The ODD protocol for describing agent-based and other simulation models: A second update to improve clarity, replication, and structural realism. *Journal of Artificial Societies and Social Simulation, 23*, 7. https://doi.org/10.18564/jasss.4259
