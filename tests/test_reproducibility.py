import unittest

from ena_abm.config import ModelConfig
from ena_abm.model import EntrepreneurialNetworkActivationModel


class ReproducibilityTests(unittest.TestCase):
    def test_identical_configuration_reproduces_summary_and_events(self):
        config = ModelConfig(master_seed=998877, replicate_id=4)
        first = EntrepreneurialNetworkActivationModel(config).run()
        second = EntrepreneurialNetworkActivationModel(config).run()
        self.assertEqual(first.summary, second.summary)
        self.assertEqual(first.events, second.events)
        self.assertEqual(first.ticks, second.ticks)

    def test_paired_strategies_share_initialization(self):
        base = ModelConfig(master_seed=24680, replicate_id=3)
        direct = EntrepreneurialNetworkActivationModel(
            base.with_updates(strategy="direct")
        )
        referral = EntrepreneurialNetworkActivationModel(
            base.with_updates(strategy="referral")
        )
        self.assertEqual(
            direct.initialization_signature, referral.initialization_signature
        )

    def test_budget_is_conserved(self):
        config = ModelConfig(action_budget=7, actions_per_tick=2, horizon=10)
        output = EntrepreneurialNetworkActivationModel(config).run()
        self.assertLessEqual(output.summary["actions_used"], 7)
        self.assertTrue(
            all(record["actions_this_tick"] <= 2 for record in output.ticks)
        )

    def test_equal_budget_conserves_cost(self):
        config = ModelConfig(
            fairness_criterion="equal_budget",
            budget_limit=5.0,
            direct_action_cost=2.0,
            strategy="direct",
            action_budget=99,
            horizon=10,
        )
        output = EntrepreneurialNetworkActivationModel(config).run()
        self.assertLessEqual(output.summary["cost_spent"], 5.0)
        self.assertEqual(output.summary["actions_used"], 2)

    def test_equal_exposures_conserves_quota(self):
        config = ModelConfig(
            fairness_criterion="equal_exposures",
            exposure_quota=3,
            strategy="direct",
            action_budget=99,
            horizon=10,
        )
        output = EntrepreneurialNetworkActivationModel(config).run()
        self.assertEqual(output.summary["exposures_delivered"], 3)

    def test_paired_initialization_is_independent_of_fairness_criterion(self):
        base = ModelConfig(master_seed=97531, replicate_id=8)
        action_model = EntrepreneurialNetworkActivationModel(
            base.with_updates(fairness_criterion="equal_actions")
        )
        budget_model = EntrepreneurialNetworkActivationModel(
            base.with_updates(fairness_criterion="equal_budget")
        )
        exposure_model = EntrepreneurialNetworkActivationModel(
            base.with_updates(fairness_criterion="equal_exposures")
        )
        self.assertEqual(
            action_model.initialization_signature,
            budget_model.initialization_signature,
        )
        self.assertEqual(
            action_model.initialization_signature,
            exposure_model.initialization_signature,
        )


if __name__ == "__main__":
    unittest.main()
