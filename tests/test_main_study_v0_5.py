from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_main_study_v0_5.py"
SPEC = importlib.util.spec_from_file_location("run_main_study_v0_5", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class MainStudyV05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            (ROOT / "configs" / "main_study_v0.5.json").read_text(
                encoding="utf-8"
            )
        )

    def test_lhs_is_deterministic(self):
        first = MODULE.deterministic_lhs_profiles(
            self.config["main_design"], self.config["experiment_seed"]
        )
        second = MODULE.deterministic_lhs_profiles(
            self.config["main_design"], self.config["experiment_seed"]
        )
        self.assertEqual(first, second)

    def test_network_assignment_is_balanced(self):
        profiles = MODULE.deterministic_lhs_profiles(
            self.config["main_design"], self.config["experiment_seed"]
        )
        counts = Counter(
            profile["updates"]["network_type"] for profile in profiles
        )
        self.assertEqual(set(counts.values()), {32})

    def test_profile_ranges_and_discrete_parameters(self):
        profiles = MODULE.deterministic_lhs_profiles(
            self.config["main_design"], self.config["experiment_seed"]
        )
        ranges = self.config["main_design"]["parameter_ranges"]
        for profile in profiles:
            for name, (low, high) in ranges.items():
                value = profile["updates"][name]
                self.assertGreaterEqual(value, low)
                self.assertLessEqual(value, high)
            self.assertIsInstance(profile["updates"]["budget_limit"], int)
            self.assertIsInstance(profile["updates"]["seed_adopters"], int)

    def test_cost_grid_and_replication_are_preregistered(self):
        self.assertEqual(self.config["replicates"], 400)
        grid = self.config["relative_cost"]["coarse_grid"]
        self.assertEqual(grid[0], 0.25)
        self.assertEqual(grid[-1], 3.00)
        self.assertEqual(self.config["relative_cost"]["refinement_tolerance"], 0.05)

    def test_primary_and_secondary_accounting_are_distinct(self):
        self.assertEqual(self.config["primary_accounting"], "upfront_expected")
        self.assertEqual(self.config["secondary_accounting"], "staged")


if __name__ == "__main__":
    unittest.main()
