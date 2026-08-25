# Decision Log v0.5

## D-001 — Scientific status

**Decision:** Execute v0.5 as the main theoretical simulation study using
diagnostic parameters.

**Reason:** The research objective is to close the thesis-derived theoretical
cycle without claiming empirical calibration.

## D-002 — Frozen behavioral architecture

**Decision:** Preserve the complete v0.4 model source and use it unchanged.

**Reason:** Version 0.4 already verified cost separation, the
attempt-to-exposure chain, fairness, and reproducibility.

## D-003 — Primary accounting

**Decision:** Retain full expected cost at attempt initiation as primary;
retain stage-based realized cost as secondary robustness.

**Reason:** This is the authorized interpretation of \(r\) as total expected
cost per initiated attempt. Stage shares remain diagnostic.

## D-004 — Main experimental design

**Decision:** Use 96 deterministic stratified Latin-hypercube profiles balanced
over three network structures.

**Reason:** Morris screening indicated nonlinear and interacting effects. A
space-filling design covers the nine prioritized ranges without an
unnecessarily large factorial.

## D-005 — Replication and pairing

**Decision:** Use 400 paired replications per profile-cost cell.

**Reason:** The v0.4 precision pilot found that 200 met MCSE criteria but not
the threshold-stability criterion when doubled.

## D-006 — Cost threshold

**Decision:** Search \(r\in[0.25,3.00]\) on a 0.25 grid and refine all crossing
brackets to 0.05.

**Reason:** This preserves the v0.4 definition and prevents post-hoc selection
of favorable thresholds.

## D-007 — Extreme and null results

**Decision:** Retain all valid zero-adoption, extinction, no-opportunity, and
boundary runs.

**Reason:** They define theoretical limits and are not simulation failures.

## D-008 — Sensitivity

**Decision:** Combine bootstrap uncertainty, rank associations, nonlinear
emulation, and shallow descriptive classification.

**Reason:** This separates Monte Carlo uncertainty from parameter sensitivity
and avoids treating Morris screening as the definitive analysis.

## Pending execution entries

Observed results, stopping-rule diagnostics, robustness findings, and
reproduction hashes will be appended without modifying the decisions above.

## D-009 — Fixed-cost protocol correction

**Observed issue:** The design declared a comparison at \(r=1.20\), but the
coarse grid omitted that exact point. Refinement generated it only for some
profiles.

**Decision:** Before sensitivity or substantive interpretation, execute
\(r=1.20\) for all 96 profiles in a separate registered output using the same
profile-specific seeds and 400 paired replications.

**Consequence:** Primary curves, thresholds, bootstrap results, and stopping
rules remain unchanged. The correction is documented in
`PROTOCOL_CORRECTION_v0.5.md`.

## D-010 — Main result

**Observed:** Ninety-one of 96 profiles produced finite interpretable
thresholds. The median primary \(r^*\) was 1.05, with IQR [1.00, 1.20] and
finite range [0.85, 2.80]. Four profiles had no competitive tested region and
one remained competitive through \(r=3.00\). No profile had multiple
crossings.

**Decision:** Report a distribution of conditional thresholds rather than a
universal break-even point.

## D-011 — Equal-cost and v0.4-threshold contrasts

**Observed:** At \(r=1.00\), referrals was competitive in 77.1% of the
registered theoretical profiles and the mean profile-level difference was
+0.49 adoptions. At \(r=1.20\), it was competitive in 26.0% and the mean
difference was -0.81.

**Decision:** Use both contrasts in the article and state explicitly that the
profile shares describe the experimental design space, not real-market
prevalence.

## D-012 — Sensitivity interpretation

**Observed:** Market sociality, initial uncertainty, and the social coefficient
showed the largest rank associations and nonlinear permutation importance.
The random-forest emulator had mean five-fold cross-validated
\(R^2=0.20\), with high fold variability.

**Decision:** Treat the emulator ranking as exploratory. Base central claims on
direct simulated contrasts, threshold distributions, boundary scenarios, and
rank associations rather than surrogate predictions.

## D-013 — Cost-accounting robustness

**Observed:** The median absolute staged-versus-upfront threshold difference
was 0.10. One of nine contexts—abundant budget—differed by 0.25.

**Decision:** The accounting convention does not reverse the central
conclusion. Upfront expected cost remains primary; staged cost is reported as a
secondary theoretical robustness analysis.

## D-014 — Reproducibility

**Observed:** Both independent runs produced 972,800 paired rows. Seven raw
gzip files initially differed only because of timestamp metadata in their
headers; all decompressed SHA-256 hashes matched. After canonicalizing gzip
headers to `mtime=0`, all 34 principal outputs were byte-identical.

**Decision:** Accept complete computational reproducibility. Preserve the
canonical compression routine in the v0.5 code.
