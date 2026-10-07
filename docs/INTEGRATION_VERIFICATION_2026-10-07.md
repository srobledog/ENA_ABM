# Extension integration verification — 2026-10-07

Base: `e45d11f03da12c67c756f00794041ab1fc7d6dff` (v0.5.0).
Extension reviewed: `afb9d9e24915d41ffc11d43c29667aab4b310d6e`.
The extension contains nine commits beyond the base and no divergent base commits.

Review covered the added mechanism controls, signed social components,
paired analysis, checkpoint/backup handling and their automated tests. The
original model files are unchanged; the extension inherits the base model.
NumPy >=2,<3 is added for analysis. Historical configurations and result
reports retain their original execution identities.

The first Windows test run passed 94 of 95 tests. The recovery test failed
because the manifest stored Windows backslash paths while its integrity
check looked up forward-slash paths. Manifest keys now use `Path.as_posix()`.
The existing recovery test additionally checks that portable keys are present.
This changes path serialization, not model rules, parameters or statistical
estimands. Existing scientific outputs were not rewritten.

Validation: `PYTHONPATH=src python -m unittest discover -s tests -v`;
all 95 tests passed on Windows after the correction. Coverage includes
base-model equivalence, 60 legacy signed-control trajectories, signed component
identities, deterministic paired bootstrap on synthetic test inputs, gzip
integrity, interrupted-profile recovery and mocked backup acknowledgments.
Only bounded test fixtures were executed; no principal experiment or
bootstrap of the scientific dataset was repeated. `git diff --check` passed.

Scope limits: this is code integration, not a new audit of the archived raw
scientific traces. The historical signed main runner still assumes a Linux
`/tmp` directory, a `python3` executable and an external library-upload helper;
its full production environment is not validated by these Windows unit tests.
The v0.5.0 tag and prior execution commits remain available. No new release
or public extension-data deposit is created by this integration.
