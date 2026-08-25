import unittest

from ena_abm.break_even import (
    mapped_updates,
    refinement_grid,
    threshold_summary,
)


def summary(r, delta, mcse=0.1, probability=0.5):
    return {
        "scenario": "baseline",
        "factor": "baseline",
        "level": "diagnostic",
        "accounting": "upfront_expected",
        "r": r,
        "mean_delta": delta,
        "mcse_delta": mcse,
        "ci95_lower": delta - 1.96 * mcse,
        "probability_referral_higher": probability,
        "mean_delta_allocated_efficiency": delta / 40.0,
    }


class BreakEvenAnalysisTests(unittest.TestCase):
    def test_mean_parameters_map_to_valid_beta_shapes(self):
        updates = mapped_updates(
            {"status_mean": 0.3, "uncertainty_mean": 0.8}
        )
        self.assertAlmostEqual(updates["status_alpha"], 3.0)
        self.assertAlmostEqual(updates["status_beta"], 7.0)
        self.assertAlmostEqual(updates["uncertainty_alpha"], 8.0)
        self.assertAlmostEqual(updates["uncertainty_beta"], 2.0)

    def test_primary_threshold_is_predeclared_supremum(self):
        rows = [
            summary(0.75, 1.0, probability=0.8),
            summary(1.00, 0.2, probability=0.6),
            summary(1.25, -0.3, probability=0.4),
        ]
        threshold = threshold_summary(rows)[0]
        self.assertEqual(threshold["r_star_primary_grid"], 1.0)
        self.assertEqual(threshold["r_star_probability_grid"], 1.0)
        self.assertEqual(threshold["crossing_count"], 1)

    def test_conservative_threshold_uses_lower_confidence_limit(self):
        rows = [
            summary(0.75, 0.5, mcse=0.1),
            summary(1.00, 0.1, mcse=0.1),
            summary(1.25, -0.4, mcse=0.1),
        ]
        threshold = threshold_summary(rows)[0]
        self.assertEqual(threshold["r_star_conservative_grid"], 0.75)

    def test_refinement_grid_fills_crossing_bracket(self):
        rows = [summary(1.0, 0.2), summary(1.25, -0.3)]
        refined = refinement_grid(rows, tolerance=0.05)
        self.assertEqual(
            refined[("baseline", "upfront_expected")],
            [1.05, 1.1, 1.15, 1.2],
        )

    def test_multiple_crossings_are_not_forced_to_one_threshold(self):
        rows = [
            summary(0.5, 1.0),
            summary(1.0, -0.2),
            summary(1.5, 0.1),
            summary(2.0, -0.5),
        ]
        threshold = threshold_summary(rows)[0]
        self.assertEqual(threshold["crossing_count"], 3)
        self.assertEqual(threshold["interpretable_single_threshold"], 0)


if __name__ == "__main__":
    unittest.main()
