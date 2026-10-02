import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from ena_abm.mechanism_analysis import (
    METRICS, PRIMARY, _bootstrap, _classification, _quantiles,
    _estimate_rows, _validate_and_matrix, _verify_gzip_csv,
    _write_gzip_csv_atomic, analyze,
)


class MechanismAnalysisTests(unittest.TestCase):
    def rows(self, profiles=("P001", "P002"), replicates=4):
        rows = []
        for pidx, profile in enumerate(profiles):
            for replicate in range(replicates):
                for cost in (1.0, 1.2):
                    for schedule in ("N", "E"):
                        base = pidx * 10 + replicate + (2 if cost == 1.2 else 0) + (1 if schedule == "E" else 0)
                        rows.append({"profile_id": profile, "replicate_id": str(replicate), "r": str(cost),
                            "schedule": schedule, "G": str(base), "G_A1": str(base - 1),
                            "G_L0": str(base - 2), "G_A0": str(base - 4),
                            "L": "999", "B": "999", "I": "999"})
        return rows

    def test_reconstructs_registered_contrasts_instead_of_trusting_derived_columns(self):
        profiles, vectors = _validate_and_matrix(self.rows(), ["P001", "P002"], 4)
        self.assertEqual(profiles, ["P001", "P002"])
        metric = METRICS.index((1.0, "N", "L"))
        interaction = METRICS.index((1.0, "N", "I"))
        q = METRICS.index((1.0, "N-E", "Q_L1"))
        self.assertTrue(np.all(vectors[:, :, metric] == 1))
        self.assertTrue(np.all(vectors[:, :, interaction] == -1))
        self.assertTrue(np.all(vectors[:, :, q] == -1))

    def test_incomplete_and_duplicate_blocks_fail(self):
        rows = self.rows(profiles=("P001",), replicates=2)
        with self.assertRaises(ValueError):
            _validate_and_matrix(rows[:-1], ["P001"], 2)
        with self.assertRaises(ValueError):
            _validate_and_matrix(rows + [rows[0]], ["P001"], 2)

    def test_bootstrap_is_deterministic_and_preserves_block_relations(self):
        profiles, vectors = _validate_and_matrix(self.rows(), ["P001", "P002"], 4)
        first = _bootstrap(vectors, profiles, 101, 2026100202, chunk_size=17)
        second = _bootstrap(vectors, profiles, 101, 2026100202, chunk_size=23)
        np.testing.assert_array_equal(first, second)
        g = METRICS.index((1.0, "N", "G")); l = METRICS.index((1.0, "N", "L"))
        np.testing.assert_array_equal(first[:, :, l], np.ones((2, 101)))
        self.assertGreater(np.ptp(first[:, :, g]), 0)

    def test_linear_intervals_and_protocol_classifications(self):
        low, high = _quantiles(np.arange(10000.0), adjusted=True)
        self.assertAlmostEqual(low, 31.246875)
        self.assertAlmostEqual(high, 9967.753125)
        self.assertEqual(_classification(.6, 1.2, .5), "positive_diagnostic")
        self.assertEqual(_classification(-.4, .3, .5), "equivalent_within_margin")
        self.assertEqual(_classification(.1, .8, .5), "sign_supported_relevance_uncertain")
        self.assertEqual(_classification(-1, 1, .5), "inconclusive")

    def test_primary_family_is_exactly_eight(self):
        self.assertEqual(len(PRIMARY), 8)
        self.assertTrue(all(schedule == "N" for _, schedule, _ in PRIMARY))

    def test_adjusted_intervals_exist_only_for_eight_primary_count_estimands(self):
        profiles = ["P001", "P002"]
        point = np.zeros((2, len(METRICS)))
        boot = np.zeros((2, 20, len(METRICS)))
        metadata = {
            profile: {"network_type": "random", "market_sociality": .5,
                "budget_limit": 10, "seed_adopters": 5, "percentage_factor": 100 / 95}
            for profile in profiles
        }
        _, rows = _estimate_rows(profiles, point, boot, metadata, margin=.5)
        adjusted = [row for row in rows if row["ci99_375_bonferroni_low"]]
        self.assertEqual(len(adjusted), 8)
        self.assertTrue(all(row["scale"] == "new_adopters" for row in adjusted))

    def test_gzip_csv_is_atomic_complete_and_crc_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bootstrap.csv.gz"
            metadata = _write_gzip_csv_atomic(
                path, ["sample", "value"],
                ({"sample": index, "value": index / 7} for index in range(100)),
                expected_rows=100,
            )
            self.assertEqual(metadata["rows"], 100)
            self.assertGreater(metadata["uncompressed_bytes"], 0)
            self.assertFalse(path.with_name(path.name + ".part").exists())
            with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 100)
            data = path.read_bytes()
            path.write_bytes(data[:-8])
            with self.assertRaises((EOFError, gzip.BadGzipFile)):
                _verify_gzip_csv(path, 100)

    def test_pilot_analysis_requires_explicit_technical_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input").mkdir()
            (root / "input/manifest.json").write_text(json.dumps({"stage": "pilot"}))
            (root / "spec.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "main-stage"):
                analyze(root / "input", root / "output", root / "spec.json")


if __name__ == "__main__":
    unittest.main()
