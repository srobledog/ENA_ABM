# Appendix S5. Exploratory sensitivity analysis

## ENA-ABM v0.5 main theoretical experiment

This appendix reports the preregistered exploratory sensitivity analyses for the version 0.5 experiment. The analyses describe how threshold variation is organized within the deliberately constructed theoretical design space. They do not estimate causal effects, population relationships, or a decision rule validated for real ventures.

Appendix S4 reports the direct profile-level and robustness results. Those cell comparisons and process interventions carry greater interpretive weight than the surrogate models reported here.

## S5.1 Analysis samples and status

Three related analyses were conducted:

1. Spearman rank associations used the 91 profiles with finite, interpretable values of $r^*$.
2. A random-forest emulator used the same 91 finite profiles to summarize nonlinear threshold variation.
3. Shallow classification trees used all 96 registered profiles to describe competitiveness at $r=1.00$ and $r=1.20$.

The four profiles with no competitive region and the profile right-censored at $r=3.00$ were excluded from continuous-threshold sensitivity because they do not supply an observed finite response. Consequently, threshold associations are conditional on having a finite interpretable competitive boundary.

## S5.2 Rank associations with finite thresholds

### Table S5.1. Spearman associations with profile-specific $r^*$

| Design factor | Spearman $\rho$ | Two-sided $p$ |
|---|---|---|
| Market sociality | 0.621 | 4.97e-11 |
| Social-influence coefficient | 0.487 | 9.61e-07 |
| Mean initial uncertainty | 0.325 | 0.002 |
| Adoption intercept | -0.206 | 0.050 |
| Initial seed adopters | -0.204 | 0.052 |
| Allocated budget | -0.143 | 0.175 |
| Mean status-quo satisfaction | 0.129 | 0.223 |
| Individual-fit coefficient | -0.068 | 0.522 |
| Mean product fit | 0.046 | 0.666 |

*Note.* $n=91$ finite profiles. The $p$ values are descriptive only and are not corrected for multiple comparisons. The registered profiles are design points rather than a probability sample, so these values are not inferential tests about firms or markets.

Market sociality had the largest monotonic association with the threshold ($\rho=0.621$), followed by the social-influence coefficient ($\rho=0.487$) and initial uncertainty ($\rho=0.325$). These positive associations are consistent with the activation mechanism: referrals can absorb a larger cost premium when consumers rely more strongly on socially transmitted information. The smaller negative associations for the adoption intercept and number of seed adopters should not be interpreted causally because all design factors vary jointly.

## S5.3 Nonlinear emulator

The emulator used nine continuous design factors and one categorical network factor. Continuous variables were standardized, network type was one-hot encoded, and a random-forest regressor was fitted with 600 trees, a minimum leaf size of 4, and 75% of encoded features considered at each split. The experiment seed fixed all stochastic operations.

Predictive performance was evaluated using five-fold shuffled cross-validation. Mean out-of-sample $R^2$ was 0.20, with a fold-to-fold standard deviation of 0.84. This combination of low mean performance and high instability is insufficient for a continuous predictive surface or precise out-of-design prediction.

Permutation importance was then calculated after fitting the emulator to all 91 finite profiles, using 100 permutations per encoded feature. Because importance was evaluated on the fitted sample rather than within held-out folds, it is a descriptive ranking and may overstate generalizable importance.

### Table S5.2. Permutation importance for the fitted threshold emulator

| Encoded factor | Mean decrease in $R^2$ | SD |
|---|---|---|
| Social-influence coefficient | 0.360 | 0.057 |
| Mean initial uncertainty | 0.350 | 0.060 |
| Market sociality | 0.336 | 0.056 |
| Initial seed adopters | 0.009 | 0.003 |
| Individual-fit coefficient | 0.007 | 0.002 |
| Mean status-quo satisfaction | 0.006 | 0.002 |
| Adoption intercept | 0.005 | 0.001 |
| Small-world indicator | 0.005 | 0.002 |
| Mean product fit | 0.003 | 0.001 |
| Allocated budget | 0.002 | 0.001 |
| Preferential-attachment indicator | 0.000 | 0.000 |
| Ring indicator | 0.000 | 0.000 |

![Figure S5.1. Exploratory permutation importance for the fitted random-forest emulator. Bars show the mean decrease in fitted-sample $R^2$ after permutation; error bars show the standard deviation across 100 repetitions.](<s5_sources/extracted/figure_sensitivity_importance_v0.5.png>){width=92%}

The importance ranking is strongly concentrated in the social-influence coefficient, uncertainty, and market sociality. The remaining individual variables and network indicators contribute little incremental fitted-sample importance once these factors and their nonlinear interactions are represented. This does not imply that those parameters are behaviorally irrelevant; importance is conditional on the chosen design, outcome, encoding, and fitted model.

## S5.4 Descriptive competitiveness classifiers

For each fixed cost ratio, competitiveness was coded 1 when the profile-level mean paired adoption difference was nonnegative and 0 otherwise. Continuous predictors were standardized and network type was one-hot encoded. Each decision tree used class-balanced weights, maximum depth 3, minimum leaf size 8, and the fixed experiment seed. Accuracy was assessed with five-fold stratified cross-validation.

### Table S5.3. Shallow-tree classification diagnostics

| $r$ | Competitive | Share | Training accuracy | CV accuracy | Majority baseline |
|---|---|---|---|---|---|
| 1.00 | 74/96 | 77.1% | 87.5% | 70.9% | 77.1% |
| 1.20 | 25/96 | 26.0% | 95.8% | 87.5% | 74.0% |

At $r=1.00$, cross-validated accuracy (70.9%) is below the 77.1% majority-class baseline and therefore adds no demonstrated predictive value over classifying every profile as competitive. At $r=1.20$, cross-validated accuracy is 87.5%, above the 74.0% majority-class baseline, but it still describes the registered theoretical profiles rather than an externally validated population.

The exported trees use standardized split values. Table S5.4 back-transforms those values using the means and population standard deviations of the 96-profile registry. Thresholds are approximate because the exported standardized splits were rounded to three decimals. Splits whose child branches produced the same class were omitted from the simplified presentation.

### Table S5.4. Simplified descriptive rules in original parameter units

| $r$ | Order | Predicted class | Approximate raw-scale rule |
|---|---|---|---|
| 1.00 | 1 | Competitive | budget\_limit <= 29.49 |
| 1.00 | 2 | Not Competitive | budget\_limit > 29.49 AND market\_sociality <= 0.625 AND network\_type != preferential\_attachment |
| 1.00 | 3 | Competitive | all remaining branches |
| 1.20 | 1 | Not Competitive | market\_sociality <= 0.437 |
| 1.20 | 2 | Not Competitive | market\_sociality > 0.437 AND beta\_social <= 2.125 |
| 1.20 | 3 | Not Competitive | market\_sociality > 0.437 AND beta\_social > 2.125 AND uncertainty\_mean <= 0.349 |
| 1.20 | 4 | Competitive | market\_sociality > 0.437 AND beta\_social > 2.125 AND uncertainty\_mean > 0.349 |

The $r=1.20$ classifier is especially consistent with the proposed mechanism: the competitive terminal branch requires market sociality above approximately 0.437, a social-influence coefficient above 2.125, and mean uncertainty above 0.349. These cut points are tree partitions selected from this finite design and are not universal managerial thresholds.

## S5.5 Triangulation and evidentiary hierarchy

The Spearman rankings, permutation importance, and the $r=1.20$ descriptive tree converge on the same broad pattern: referral competitiveness is most favorable when market sociality, responsiveness to social influence, and uncertainty jointly strengthen the value of network-mediated information.

This convergence is supportive but not independently confirmatory because the analyses reuse the same 96-profile experiment. The evidentiary hierarchy is therefore:

1. direct paired strategy comparisons and process interventions reported in Appendix S4;
2. profile-level rank associations; and
3. emulator importance and shallow-tree rules as exploratory summaries.

The process-robustness experiment provides the clearest mechanism-focused evidence because it changes specific access conditions while holding the baseline context otherwise fixed. The sensitivity analyses cannot isolate causal effects among factors that vary together across the Latin-hypercube profiles.

## S5.6 Limitations on interpretation and use

The following restrictions apply to every result in this appendix:

1. the 96 profiles are theoretical design points, not sampled firms or markets;
2. continuous-threshold analyses exclude absent and right-censored regions;
3. reported $p$ values are descriptive and unadjusted;
4. the emulator has limited and unstable cross-validated performance;
5. permutation importance was calculated on the fitted sample;
6. tree accuracy and split values are specific to the registered design; and
7. no result should be used to predict a venture-specific $r^*$ without empirical calibration and external validation.

For these reasons, the study does not report a continuous response surface or convert the classifier splits into managerial recommendations.

## S5.7 Machine-readable analysis files

The accompanying package contains the original sensitivity outputs, Figure S5.1, and five organized tables:

1. `Table_S5_1_Spearman_Associations.csv`;
2. `Table_S5_2_Permutation_Importance.csv`;
3. `Table_S5_3_Standardization_Constants.csv`;
4. `Table_S5_4_Descriptive_Rules_Raw_Scale.csv`; and
5. `Table_S5_5_Classifier_Diagnostics.csv`.

The original standardized tree output is retained in `competitiveness_rules_v0.5.md`, and exact emulator and classification diagnostics are retained in `sensitivity_manifest_v0.5.json`.
