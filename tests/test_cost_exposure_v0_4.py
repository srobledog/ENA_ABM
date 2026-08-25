import unittest

from ena_abm.agents import Consumer, ConsumerState
from ena_abm.config import ModelConfig
from ena_abm.model import EntrepreneurialNetworkActivationModel
from ena_abm.network import Graph


def test_consumers(n, seed_ids):
    consumers = []
    for consumer_id in range(n):
        seed = consumer_id in seed_ids
        consumers.append(
            Consumer(
                consumer_id=consumer_id,
                fit=1.0,
                status_quo_satisfaction=0.0,
                uncertainty=0.5,
                initial_uncertainty=0.5,
                state=ConsumerState.ADOPTED if seed else ConsumerState.UNAWARE,
                is_seed=seed,
                awareness_time=0 if seed else None,
                adoption_time=0 if seed else None,
                acquisition_source="seed" if seed else None,
            )
        )
    return consumers


def path_graph(n):
    graph = Graph.empty(n)
    for node in range(n - 1):
        graph.add_edge(node, node + 1)
    return graph


def isolated_graph(n):
    return Graph.empty(n)


class CostAndExposureV04Tests(unittest.TestCase):
    def base_two_person(self, **updates):
        values = dict(
            n_consumers=2,
            network_type="custom",
            mean_degree=1,
            seed_adopters=1,
            fairness_criterion="equal_budget",
            budget_limit=1.0,
            action_budget=99,
            actions_per_tick=1,
            horizon=1,
            direct_action_cost=1.0,
            referral_action_cost=1.0,
            direct_exposure_probability=1.0,
            referral_acceptance_probability=1.0,
            referral_neighbor_availability_probability=1.0,
            referral_introduction_probability=1.0,
            direct_source_credibility=0.6,
            referral_source_credibility=0.6,
            master_seed=441,
            beta_0=50.0,
        )
        values.update(updates)
        return ModelConfig(**values)

    def run_two_person(self, config):
        return EntrepreneurialNetworkActivationModel(
            config,
            graph=path_graph(2),
            consumers=test_consumers(2, {0}),
        ).run()

    def test_r_one_equivalent_mechanisms_match_behavior(self):
        direct = self.run_two_person(self.base_two_person(strategy="direct"))
        referral = self.run_two_person(self.base_two_person(strategy="referral"))
        self.assertEqual(direct.summary["attempts_started"], 1)
        self.assertEqual(referral.summary["attempts_started"], 1)
        self.assertEqual(direct.summary["exposures_delivered"], 1)
        self.assertEqual(referral.summary["exposures_delivered"], 1)
        self.assertEqual(direct.summary["new_adoptions"], 1)
        self.assertEqual(referral.summary["new_adoptions"], 1)
        self.assertEqual(direct.summary["cost_spent"], referral.summary["cost_spent"])

    def test_r_below_and_above_one_are_costs_not_probabilities(self):
        cheap = self.run_two_person(
            self.base_two_person(strategy="referral", referral_action_cost=0.5)
        )
        expensive = self.run_two_person(
            self.base_two_person(
                strategy="referral",
                referral_action_cost=2.0,
                budget_limit=2.0,
            )
        )
        self.assertEqual(cheap.summary["relative_referral_cost"], 0.5)
        self.assertEqual(expensive.summary["relative_referral_cost"], 2.0)
        self.assertEqual(
            cheap.summary["referral_introduction_probability"],
            expensive.summary["referral_introduction_probability"],
        )
        self.assertEqual(cheap.summary["new_adoptions"], expensive.summary["new_adoptions"])

    def test_exactly_divisible_budget(self):
        config = ModelConfig(
            n_consumers=4,
            network_type="custom",
            mean_degree=1,
            strategy="direct",
            seed_adopters=1,
            fairness_criterion="equal_budget",
            budget_limit=6.0,
            direct_action_cost=2.0,
            action_budget=99,
            actions_per_tick=1,
            horizon=3,
            direct_exposure_probability=0.0,
        )
        result = EntrepreneurialNetworkActivationModel(
            config,
            graph=path_graph(4),
            consumers=test_consumers(4, {0}),
        ).run()
        self.assertEqual(result.summary["attempts_started"], 3)
        self.assertEqual(result.summary["cost_spent"], 6.0)
        self.assertEqual(result.summary["unused_budget"], 0.0)

    def test_residual_budget_is_recorded(self):
        config = self.base_two_person(
            strategy="direct",
            budget_limit=5.0,
            direct_action_cost=2.0,
            horizon=3,
            direct_exposure_probability=0.0,
        )
        result = self.run_two_person(config)
        self.assertEqual(result.summary["attempts_started"], 2)
        self.assertEqual(result.summary["unused_budget"], 1.0)

    def test_budget_below_action_cost_blocks_attempt(self):
        result = self.run_two_person(
            self.base_two_person(
                strategy="direct",
                budget_limit=0.9,
                direct_action_cost=1.0,
            )
        )
        self.assertEqual(result.summary["attempts_started"], 0)
        self.assertEqual(result.summary["cost_spent"], 0.0)

    def test_failed_direct_attempt_consumes_upfront_cost(self):
        result = self.run_two_person(
            self.base_two_person(
                strategy="direct",
                direct_exposure_probability=0.0,
                beta_0=-50.0,
            )
        )
        self.assertEqual(result.summary["attempts_started"], 1)
        self.assertEqual(result.summary["failed_attempts"], 1)
        self.assertEqual(result.summary["exposures_delivered"], 0)
        self.assertEqual(result.summary["cost_spent"], 1.0)

    def test_rejected_referral_consumes_upfront_cost(self):
        result = self.run_two_person(
            self.base_two_person(
                strategy="referral",
                referral_acceptance_probability=0.0,
                beta_0=-50.0,
            )
        )
        self.assertEqual(result.summary["attempts_started"], 1)
        self.assertEqual(result.summary["requests_accepted"], 0)
        self.assertEqual(result.summary["referral_rejections"], 1)
        self.assertEqual(result.summary["cost_spent"], 1.0)

    def test_referrer_without_neighbor_is_failed_attempt(self):
        config = ModelConfig(
            n_consumers=2,
            network_type="custom",
            mean_degree=1,
            strategy="referral",
            seed_adopters=1,
            fairness_criterion="equal_budget",
            budget_limit=1.0,
            action_budget=99,
            actions_per_tick=1,
            horizon=1,
        )
        result = EntrepreneurialNetworkActivationModel(
            config,
            graph=isolated_graph(2),
            consumers=test_consumers(2, {0}),
        ).run()
        self.assertEqual(result.summary["attempts_started"], 1)
        self.assertEqual(result.summary["referrer_without_eligible_neighbor"], 1)
        self.assertEqual(result.summary["exposures_delivered"], 0)

    def test_absence_of_all_referrers_is_not_an_attempt(self):
        config = ModelConfig(
            n_consumers=2,
            network_type="custom",
            mean_degree=1,
            strategy="referral",
            seed_adopters=0,
            fairness_criterion="equal_budget",
            budget_limit=2.0,
            action_budget=99,
            actions_per_tick=1,
            horizon=1,
        )
        result = EntrepreneurialNetworkActivationModel(
            config,
            graph=path_graph(2),
            consumers=test_consumers(2, set()),
        ).run()
        self.assertEqual(result.summary["attempts_started"], 0)
        self.assertEqual(result.summary["cost_spent"], 0.0)
        self.assertEqual(result.summary["unavailable_opportunities"], 1)

    def test_effective_exposure_does_not_imply_adoption(self):
        result = self.run_two_person(
            self.base_two_person(strategy="direct", beta_0=-50.0)
        )
        self.assertEqual(result.summary["exposures_delivered"], 1)
        self.assertEqual(result.summary["unique_consumers_evaluated"], 1)
        self.assertEqual(result.summary["new_adoptions"], 0)

    def test_budget_conservation_and_cost_event_sum(self):
        result = self.run_two_person(
            self.base_two_person(
                strategy="referral",
                referral_acceptance_probability=0.0,
                budget_limit=1.5,
            )
        )
        cost_events = [
            row for row in result.events if row["event_type"] == "cost"
        ]
        self.assertAlmostEqual(
            sum(float(row["cost_increment"]) for row in cost_events),
            result.summary["cost_spent"],
        )
        self.assertAlmostEqual(result.summary["budget_conservation_error"], 0.0)

    def test_attempt_acceptance_exposure_and_adoption_logs_are_separate(self):
        result = self.run_two_person(self.base_two_person(strategy="referral"))
        event_types = [row["event_type"] for row in result.events]
        self.assertIn("attempt", event_types)
        self.assertIn("exposure", event_types)
        self.assertIn("evaluation", event_types)
        attempt = [row for row in result.events if row["event_type"] == "attempt"][0]
        self.assertEqual(attempt["accepted"], 1)
        self.assertEqual(attempt["effective_exposure"], 1)

    def test_all_process_probability_bounds(self):
        fields = [
            "direct_exposure_probability",
            "referral_acceptance_probability",
            "referral_neighbor_availability_probability",
            "referral_introduction_probability",
        ]
        for field in fields:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    ModelConfig(**{field: -0.01}).validate()
                with self.assertRaises(ValueError):
                    ModelConfig(**{field: 1.01}).validate()

    def test_stage_shares_must_sum_to_one(self):
        with self.assertRaises(ValueError):
            ModelConfig(direct_followup_share=0.20).validate()
        with self.assertRaises(ValueError):
            ModelConfig(referral_followup_share=0.20).validate()

    def test_staged_rejection_charges_only_reached_activities(self):
        result = self.run_two_person(
            self.base_two_person(
                strategy="referral",
                cost_accounting="staged",
                referral_acceptance_probability=0.0,
            )
        )
        self.assertEqual(result.summary["cost_spent"], 0.5)
        self.assertEqual(result.summary["failed_attempts"], 1)

    def test_upfront_and_staged_match_behavior_when_budget_is_sufficient(self):
        upfront = self.run_two_person(
            self.base_two_person(strategy="referral", cost_accounting="upfront_expected")
        )
        staged = self.run_two_person(
            self.base_two_person(strategy="referral", cost_accounting="staged")
        )
        self.assertEqual(upfront.summary["exposures_delivered"], 1)
        self.assertEqual(staged.summary["exposures_delivered"], 1)
        self.assertEqual(upfront.summary["new_adoptions"], staged.summary["new_adoptions"])

    def test_one_attempt_cannot_generate_multiple_exposures(self):
        result = self.run_two_person(self.base_two_person(strategy="referral"))
        self.assertLessEqual(
            result.summary["exposures_delivered"],
            result.summary["attempts_started"],
        )

    def test_cost_does_not_enter_matched_adoption_utility(self):
        cheap = self.run_two_person(
            self.base_two_person(strategy="referral", referral_action_cost=0.5)
        )
        expensive = self.run_two_person(
            self.base_two_person(
                strategy="referral",
                referral_action_cost=2.0,
                budget_limit=2.0,
            )
        )
        cheap_eval = [
            row for row in cheap.events if row["event_type"] == "evaluation"
        ][0]
        expensive_eval = [
            row for row in expensive.events if row["event_type"] == "evaluation"
        ][0]
        self.assertEqual(cheap_eval["utility"], expensive_eval["utility"])
        self.assertEqual(cheap_eval["probability"], expensive_eval["probability"])

    def test_determinism_with_fixed_seed_includes_process_events(self):
        config = ModelConfig(
            strategy="referral",
            fairness_criterion="equal_budget",
            budget_limit=10.0,
            referral_acceptance_probability=0.63,
            referral_neighbor_availability_probability=0.71,
            referral_introduction_probability=0.82,
            master_seed=987654,
        )
        first = EntrepreneurialNetworkActivationModel(config).run()
        second = EntrepreneurialNetworkActivationModel(config).run()
        self.assertEqual(first.summary, second.summary)
        self.assertEqual(first.ticks, second.ticks)
        self.assertEqual(first.events, second.events)


if __name__ == "__main__":
    unittest.main()
