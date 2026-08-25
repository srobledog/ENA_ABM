# Appendix S4. Additional results

## ENA-ABM v0.5 main theoretical experiment

This appendix reports the complete profile-level threshold classification and the prespecified robustness results from the frozen version 0.5 experiment. Appendix S1 describes the model, Appendix S2 documents the preregistered design, and Appendix S3 defines its parameters and configuration. The results below describe the registered theoretical design space; they are not estimates of prevalence or causal effects in real markets.

The accompanying machine-readable tables preserve full numeric precision. Values in the formatted tables are rounded for readability. New adopters exclude seed adopters, and $\Delta$ denotes referral minus direct new adoptions under paired simulation.

## S4.1 Threshold distribution and bootstrap stability

Of the 96 registered profiles, 91 produced a finite interpretable threshold, four had no competitive referral region within the tested interval, and one remained competitive through the upper boundary $r=3.00$. No profile exhibited multiple crossings. Among finite thresholds, the median $r^*$ was 1.05, the interquartile range was [1.00, 1.20], and the finite range was [0.85, 2.80]. The median paired-bootstrap interval width was 0.10; 3 profiles (3.1% of all registered profiles) had width greater than 0.50.

### Table S4.1. Complete profile-level thresholds, bootstrap intervals, and fixed-cost adoption differences

| Profile | Net. | $r^*$ | Class | Bootstrap 95% interval | $\Delta$ at 1.00 | $\Delta$ at 1.20 |
|---|---|---|---|---|---|---|
| P001 | PA | 1.10 | finite threshold | [1.05, 1.15] | 0.71 | -0.44 |
| P002 | SW | — | no region | — | -2.02 | -4.63 |
| P003 | R | 0.95 | finite threshold | [0.95, 1.00] | -0.14 | -2.28 |
| P004 | R | 1.45 | finite threshold | [1.45, 1.50] | 2.47 | 1.17 |
| P005 | PA | 1.00 | finite threshold | [1.00, 1.10] | 0.16 | -0.24 |
| P006 | SW | 1.45 | finite threshold | [1.35, 1.50] | 1.13 | 0.55 |
| P007 | PA | 1.00 | finite threshold | [0.75, 1.05] | 0.21 | -0.87 |
| P008 | PA | 1.05 | finite threshold | [1.00, 1.05] | 0.27 | -0.62 |
| P009 | R | 1.25 | finite threshold | [1.00, 1.35] | 0.54 | 0.14 |
| P010 | PA | 1.15 | finite threshold | [1.10, 1.20] | 1.04 | -0.20 |
| P011 | SW | 1.30 | finite threshold | [1.00, 1.35] | 0.51 | 0.10 |
| P012 | R | 1.05 | finite threshold | [1.00, 1.15] | 0.27 | -0.25 |
| P013 | SW | 1.00 | finite threshold | [0.75, 1.00] | 0.02 | -0.91 |
| P014 | PA | 1.00 | finite threshold | [1.00, 1.05] | 0.54 | -1.42 |
| P015 | R | 0.90 | finite threshold | [0.90, 0.95] | -0.41 | -2.32 |
| P016 | R | 1.10 | finite threshold | [1.05, 1.15] | 0.43 | -0.17 |
| P017 | PA | 1.00 | finite threshold | [0.75, 1.00] | 0.10 | -0.86 |
| P018 | R | 1.20 | finite threshold | [1.05, 1.25] | 0.38 | 0.08 |
| P019 | PA | 0.95 | finite threshold | [0.95, 1.00] | -0.14 | -1.23 |
| P020 | SW | 0.90 | finite threshold | [0.90, 0.95] | -0.58 | -2.79 |
| P021 | R | 0.95 | finite threshold | [0.90, 1.00] | -0.03 | -0.65 |
| P022 | R | 1.40 | finite threshold | [1.35, 1.45] | 2.52 | 1.02 |
| P023 | PA | 1.00 | finite threshold | [1.00, 1.05] | 0.39 | -1.84 |
| P024 | PA | 1.00 | finite threshold | [0.75, 1.00] | 0.04 | -0.23 |
| P025 | PA | 1.70 | finite threshold | [1.25, 2.00] | 0.19 | 0.12 |
| P026 | SW | — | no region | [0.75, 0.75] | -1.41 | -3.63 |
| P027 | R | 1.00 | finite threshold | [0.75, 1.00] | 0.20 | -0.98 |
| P028 | R | 1.20 | finite threshold | [1.10, 1.20] | 0.71 | 0.07 |
| P029 | SW | — | no region | — | -1.87 | -4.83 |
| P030 | PA | 1.15 | finite threshold | [1.05, 1.25] | 0.32 | -0.03 |
| P031 | PA | 1.30 | finite threshold | [1.30, 1.35] | 3.58 | 1.09 |
| P032 | R | 0.95 | finite threshold | [0.90, 0.95] | -0.42 | -2.62 |
| P033 | SW | 1.05 | finite threshold | [1.00, 1.05] | 1.14 | -1.56 |
| P034 | R | 1.05 | finite threshold | [1.05, 1.10] | 0.70 | -0.55 |
| P035 | SW | 0.95 | finite threshold | [0.90, 1.00] | -0.19 | -2.35 |
| P036 | SW | 0.90 | finite threshold | [0.90, 1.00] | -0.02 | -0.57 |
| P037 | R | 1.45 | finite threshold | [1.40, 1.45] | 2.57 | 1.17 |
| P038 | PA | 1.00 | finite threshold | [0.75, 1.00] | 0.09 | -0.35 |
| P039 | SW | 1.50 | finite threshold | [1.25, 1.60] | 0.98 | 0.50 |
| P040 | SW | 1.30 | finite threshold | [1.00, 1.30] | 0.76 | 0.10 |
| P041 | PA | 1.15 | finite threshold | [1.10, 1.20] | 1.42 | -0.10 |
| P042 | R | 1.00 | finite threshold | [1.00, 1.00] | 0.28 | -0.93 |
| P043 | PA | 1.00 | finite threshold | [0.75, 1.00] | 0.13 | -1.71 |
| P044 | PA | — | no region | — | -2.48 | -5.92 |
| P045 | SW | 1.00 | finite threshold | [1.00, 1.05] | 0.32 | -0.85 |
| P046 | SW | 1.40 | finite threshold | [1.30, 1.50] | 0.83 | 0.39 |
| P047 | SW | 1.75 | finite threshold | [1.50, 2.00] | 1.71 | 1.00 |
| P048 | R | 1.15 | finite threshold | [1.05, 1.20] | 0.76 | -0.24 |
| P049 | R | 0.90 | finite threshold | [0.90, 0.95] | -0.60 | -3.06 |
| P050 | R | 1.05 | finite threshold | [1.05, 1.10] | 1.07 | -0.98 |
| P051 | PA | 1.05 | finite threshold | [1.00, 1.10] | 0.38 | -0.43 |
| P052 | SW | 1.05 | finite threshold | [1.00, 1.05] | 0.35 | -0.60 |
| P053 | PA | 1.40 | finite threshold | [1.00, 1.50] | 0.41 | 0.20 |
| P054 | SW | 1.35 | finite threshold | [1.30, 1.45] | 1.11 | 0.38 |
| P055 | SW | 0.90 | finite threshold | [0.90, 0.90] | -1.28 | -5.05 |
| P056 | PA | 1.00 | finite threshold | [0.75, 1.00] | 0.06 | -0.40 |
| P057 | PA | 1.05 | finite threshold | [1.00, 1.15] | 0.24 | -0.14 |
| P058 | PA | 1.05 | finite threshold | [1.00, 1.10] | 0.71 | -0.81 |
| P059 | PA | 1.40 | finite threshold | [1.35, 1.50] | 1.70 | 0.73 |
| P060 | R | 1.10 | finite threshold | [1.10, 1.15] | 1.19 | -0.59 |
| P061 | PA | 1.00 | finite threshold | [1.00, 1.05] | 0.32 | -0.68 |
| P062 | R | 1.05 | finite threshold | [1.00, 1.05] | 0.35 | -0.63 |
| P063 | PA | 1.05 | finite threshold | [1.00, 1.05] | 0.73 | -1.52 |
| P064 | R | 0.85 | finite threshold | [0.80, 0.90] | -1.20 | -3.10 |
| P065 | SW | 2.50 | finite threshold | [2.25, 3.00] | 1.85 | 1.30 |
| P066 | R | 1.40 | finite threshold | [1.30, 1.45] | 0.94 | 0.47 |
| P067 | R | 1.00 | finite threshold | [0.75, 1.00] | 0.00 | -1.61 |
| P068 | SW | 0.90 | finite threshold | [0.85, 1.00] | -0.12 | -0.51 |
| P069 | R | 1.00 | finite threshold | [0.75, 1.00] | 0.03 | -0.54 |
| P070 | R | 1.05 | finite threshold | [1.00, 1.20] | 0.17 | -0.08 |
| P071 | SW | 1.05 | finite threshold | [1.00, 1.10] | 0.61 | -0.99 |
| P072 | SW | 2.80 | finite threshold | [2.00, 3.00] | 0.70 | 0.50 |
| P073 | SW | 1.05 | finite threshold | [1.05, 1.10] | 1.24 | -1.22 |
| P074 | R | 0.95 | finite threshold | [0.90, 0.95] | -0.47 | -2.77 |
| P075 | R | 1.35 | finite threshold | [1.25, 1.35] | 0.77 | 0.24 |
| P076 | SW | 1.00 | finite threshold | [1.00, 1.05] | 0.57 | -1.32 |
| P077 | SW | 0.95 | finite threshold | [0.90, 0.95] | -0.42 | -3.45 |
| P078 | R | 3.00 | right-censored | [2.50, 3.00] | 4.41 | 2.88 |
| P079 | SW | 0.90 | finite threshold | [0.90, 0.95] | -0.86 | -3.41 |
| P080 | PA | 1.00 | finite threshold | [0.75, 1.05] | 0.00 | -0.59 |
| P081 | SW | 1.00 | finite threshold | [1.00, 1.05] | 0.33 | -0.56 |
| P082 | PA | 1.00 | finite threshold | [1.00, 1.05] | 0.34 | -1.17 |
| P083 | PA | 1.05 | finite threshold | [1.00, 1.10] | 0.27 | -0.65 |
| P084 | PA | 1.15 | finite threshold | [1.10, 1.20] | 1.03 | -0.18 |
| P085 | PA | 1.00 | finite threshold | [0.75, 1.00] | 0.03 | -1.56 |
| P086 | SW | 1.00 | finite threshold | [1.00, 1.00] | 0.36 | -1.72 |
| P087 | SW | 0.95 | finite threshold | [0.95, 1.00] | -0.18 | -1.00 |
| P088 | R | 1.15 | finite threshold | [1.15, 1.25] | 0.86 | -0.04 |
| P089 | SW | 2.55 | finite threshold | [2.25, 2.75] | 4.54 | 3.19 |
| P090 | R | 1.30 | finite threshold | [1.00, 1.30] | 1.74 | 0.46 |
| P091 | SW | 1.15 | finite threshold | [1.10, 1.15] | 0.79 | -0.28 |
| P092 | SW | 0.90 | finite threshold | [0.85, 0.90] | -1.22 | -3.39 |
| P093 | R | 1.00 | finite threshold | [0.75, 1.05] | 0.10 | -1.04 |
| P094 | PA | 1.05 | finite threshold | [1.00, 1.10] | 0.54 | -0.68 |
| P095 | R | 1.80 | finite threshold | [1.50, 1.90] | 3.79 | 2.32 |
| P096 | PA | 0.90 | finite threshold | [0.90, 0.95] | -0.34 | -1.53 |

*Note.* PA = preferential attachment; R = ring; SW = small world. The bootstrap interval is the 2.5th–97.5th percentile interval from 500 paired resamples. An absent interval is retained for profiles with no finite bootstrap threshold. The complete machine-readable table also includes alternative threshold definitions, classification flags, bootstrap probabilities, confidence intervals, exposure measures, and conversion measures.

### Table S4.2. Threshold distribution by network structure

| Network | Profiles | Finite | Median $r^*$ | IQR | Finite range |
|---|---|---|---|---|---|
| Preferential Attachment | 32 | 31 | 1.05 | [1.00, 1.12] | [0.90, 1.70] |
| Ring | 32 | 31 | 1.05 | [1.00, 1.23] | [0.85, 1.80] |
| Small World | 32 | 29 | 1.05 | [0.95, 1.35] | [0.90, 2.80] |

Network medians are similar, but this comparison does not isolate a causal network effect because the profile design varies several factors simultaneously.

## S4.2 Fixed-cost comparisons

### Table S4.3. Principal outcomes at equal cost and at a 20% referral premium

| $r$ | Competitive profiles | Competitive share | Mean $\Delta$ | Mean direct adoptions | Mean referral adoptions | Mean $P(Y_R>Y_D)$ |
|---|---|---|---|---|---|---|
| 1.00 | 74/96 | 77.1% | 0.49 | 6.58 | 7.07 | 48.0% |
| 1.20 | 25/96 | 26.0% | -0.81 | 6.58 | 5.77 | 30.7% |

*Note.* “Competitive” means a nonnegative profile-level mean paired adoption difference. The competitive share describes the 96 deliberately constructed profiles, not the share of firms or markets in a population. Means are averages of the 96 profile-level cell means. The $r=1.20$ values come from the separately documented completion of the preregistered fixed-cost contrast.

At equal attempt cost, referrals were competitive in 74 profiles (77.1%) and produced 0.49 additional adoptions on average. At $r=1.20$, referrals were competitive in 25 profiles (26.0%) and the average difference was -0.81.

## S4.3 Exposure-process robustness

### Table S4.4. Referral cost thresholds by process regime and network structure

| Process regime | Preferential attachment | Ring | Small world |
|---|---|---|---|
| Neutral baseline | 1.10 | 1.25 | 1.20 |
| Equal high exposure | 1.00 | 1.15 | 1.10 |
| Referral-exposure advantage | 1.60 | 1.80 | 1.65 |
| Direct-exposure advantage | No competitive region | 0.75 | 0.65 |
| High acceptance | 1.35 | 1.50 | 1.45 |
| Low acceptance | No competitive region | No competitive region | No competitive region |
| Abundant eligible neighbors | 1.35 | 1.60 | 1.45 |
| No eligible neighbors | No competitive region | No competitive region | No competitive region |

*Note.* Entries are the largest tested cost ratios with a nonnegative mean paired adoption difference. “No competitive region” means that referrals did not reach parity anywhere in the evaluated range. Low acceptance and the absence of eligible neighbors eliminated the competitive region in every network. A referral-exposure advantage increased the finite thresholds, whereas a direct-exposure advantage removed the region in preferential attachment and lowered it in the other networks.

## S4.4 Accounting robustness

### Table S4.5. Upfront and staged-accounting thresholds

| Context | Upfront $r^*$ | Staged $r^*$ | Difference |
|---|---|---|---|
| Baseline | 1.15 | 1.25 | 0.10 |
| Sociality Low | 0.95 | 1.00 | 0.05 |
| Sociality High | 1.50 | 1.60 | 0.10 |
| Budget Scarce | 1.10 | 1.20 | 0.10 |
| Budget Abundant | 1.15 | 1.40 | 0.25 |
| Referrers Scarce | 1.25 | 1.30 | 0.05 |
| Referrers Abundant | 1.10 | 1.15 | 0.05 |
| Network Ring | 1.20 | 1.25 | 0.05 |
| Network Preferential Attachment | 1.05 | 1.15 | 0.10 |

*Note.* Staged minus upfront. Staged accounting increased the threshold by a median of 0.10. Eight contexts differed by 0.05 or 0.10; the abundant-budget context was the only one reaching the prespecified material difference of 0.25. The diagnostic stage shares are not empirical cost estimates.

## S4.5 Structural robustness

### Table S4.6. Thresholds under structural variants

| Context | Primary $r^*$ | Conservative $r^*$ | Probability $r^*$ |
|---|---|---|---|
| Baseline | 1.20 | 1.15 | 1.10 |
| Network Size Small | 1.00 | 0.75 | 0.75 |
| Network Size Large | 1.25 | 1.00 | 1.00 |
| Mean Degree Low | 1.25 | 1.00 | 1.00 |
| Mean Degree High | 1.15 | 1.10 | 1.10 |
| Rewiring Zero | 1.25 | 1.00 | 1.00 |
| Rewiring High | 1.10 | 1.05 | 1.05 |
| Network Ring | 1.25 | 1.00 | 1.00 |
| Network Preferential Attachment | 1.05 | 1.00 | 1.00 |

*Note.* Structural contexts alter existing model parameters only. Primary thresholds ranged from 1.00 to 1.25. All nine contexts retained a finite, single competitive threshold.

## S4.6 Robustness to takeoff and extinction definitions

### Table S4.7. Dynamic classifications under alternative definitions

| Takeoff share | Quiet ticks | $r$ | Mean $\Delta$ | Direct takeoff | Referral takeoff | Direct extinction | Referral extinction |
|---|---|---|---|---|---|---|---|
| 5% | 10 | 1.00 | 1.51 | 77.2% | 87.8% | 22.8% | 11.8% |
| 5% | 10 | 1.20 | -0.04 | 77.2% | 76.2% | 22.8% | 23.8% |
| 5% | 3 | 1.00 | 1.49 | 74.5% | 87.2% | 25.5% | 12.8% |
| 5% | 3 | 1.20 | -0.07 | 74.5% | 72.8% | 25.5% | 27.3% |
| 5% | 5 | 1.00 | 1.54 | 71.8% | 86.5% | 28.2% | 13.5% |
| 5% | 5 | 1.20 | 0.07 | 71.8% | 75.2% | 28.2% | 24.8% |
| 10% | 10 | 1.00 | 1.42 | 12.5% | 28.0% | 82.2% | 69.0% |
| 10% | 10 | 1.20 | -0.01 | 12.5% | 12.2% | 82.2% | 87.8% |
| 10% | 3 | 1.00 | 1.43 | 14.0% | 28.2% | 86.0% | 71.8% |
| 10% | 3 | 1.20 | -0.06 | 14.0% | 11.0% | 86.0% | 89.0% |
| 10% | 5 | 1.00 | 1.47 | 12.8% | 30.0% | 87.2% | 70.0% |
| 10% | 5 | 1.20 | 0.05 | 12.8% | 13.5% | 87.2% | 86.5% |
| 15% | 10 | 1.00 | 1.33 | 0.5% | 1.0% | 94.2% | 91.0% |
| 15% | 10 | 1.20 | -0.03 | 0.5% | 0.2% | 94.2% | 99.8% |
| 15% | 3 | 1.00 | 1.73 | 0.2% | 1.2% | 99.8% | 98.8% |
| 15% | 3 | 1.20 | 0.21 | 0.2% | 0.0% | 99.8% | 100.0% |
| 15% | 5 | 1.00 | 1.39 | 1.0% | 0.8% | 99.0% | 99.2% |
| 15% | 5 | 1.20 | -0.01 | 1.0% | 0.0% | 99.0% | 100.0% |
| 20% | 10 | 1.00 | 1.51 | 0.0% | 0.0% | 92.2% | 88.2% |
| 20% | 10 | 1.20 | 0.03 | 0.0% | 0.0% | 92.2% | 100.0% |
| 20% | 3 | 1.00 | 1.14 | 0.0% | 0.0% | 100.0% | 100.0% |
| 20% | 3 | 1.20 | -0.18 | 0.0% | 0.0% | 100.0% | 100.0% |
| 20% | 5 | 1.00 | 1.50 | 0.0% | 0.0% | 100.0% | 100.0% |
| 20% | 5 | 1.20 | -0.10 | 0.0% | 0.0% | 100.0% | 100.0% |

*Note.* Each row contains 400 paired replications of the predefined baseline context. Alternative takeoff shares and quiet periods concern classification of dynamic outcomes rather than a new behavioral mechanism. The mean adoption difference is included as a diagnostic for each separately generated paired cell and should not be interpreted as an effect of changing the takeoff or extinction definition.

## S4.7 Machine-readable tables and interpretation boundary

The accompanying data-table package contains the following files:

1. `Table_S4_1_Profile_Thresholds_Bootstrap_Fixed_Cost.csv`: all 96 profiles, four threshold definitions, classification flags, bootstrap results, and detailed cells at $r=1.00$ and $r=1.20$;
2. `Table_S4_2_Fixed_Cost_Aggregates.csv`: aggregate descriptive comparisons at $r=1.00$ and $r=1.20$;
3. `Table_S4_3_Process_Robustness.csv`: all 24 network-by-process threshold cells;
4. `Table_S4_4_Accounting_Robustness.csv`: the nine accounting comparisons;
5. `Table_S4_5_Structural_Robustness.csv`: the nine structural contexts; and
6. `Table_S4_6_Dynamic_Definitions.csv`: all 24 takeoff/quiet-period classifications.

These tables report outcomes of a reproducible theoretical experiment with diagnostic parameters. They do not establish the empirical frequency of referral advantage, estimate a universal customer-acquisition premium, or justify applying the median threshold to an individual venture without calibration.
