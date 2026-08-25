import unittest

from ena_abm.agents import Consumer, ConsumerState
from ena_abm.config import ModelConfig
from ena_abm.model import EntrepreneurialNetworkActivationModel
from ena_abm.network import Graph


def consumers_for_test(n, seed_ids):
    result = []
    for consumer_id in range(n):
        is_seed = consumer_id in seed_ids
        result.append(
            Consumer(
                consumer_id=consumer_id,
                fit=1.0,
                status_quo_satisfaction=0.0,
                uncertainty=0.5,
                initial_uncertainty=0.5,
                state=ConsumerState.ADOPTED if is_seed else ConsumerState.UNAWARE,
                is_seed=is_seed,
                awareness_time=0 if is_seed else None,
                adoption_time=0 if is_seed else None,
                acquisition_source="seed" if is_seed else None,
            )
        )
    return result


def path_graph(n):
    graph = Graph.empty(n)
    for node in range(n - 1):
        graph.add_edge(node, node + 1)
    return graph


def complete_graph(n):
    graph = Graph.empty(n)
    for a in range(n):
        for b in range(a + 1, n):
            graph.add_edge(a, b)
    return graph


def fragmented_graph():
    graph = Graph.empty(6)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    graph.add_edge(3, 4)
    return graph


class ControlledDynamicsTests(unittest.TestCase):
    def test_direct_one_action_creates_at_most_one_new_adoption(self):
        config = ModelConfig(
            n_consumers=4,
            network_type="ring",
            mean_degree=2,
            strategy="direct",
            market_sociality=0.0,
            seed_adopters=1,
            action_budget=1,
            actions_per_tick=1,
            horizon=1,
            beta_0=50.0,
        )
        output = EntrepreneurialNetworkActivationModel(
            config,
            graph=path_graph(4),
            consumers=consumers_for_test(4, {0}),
        ).run()
        self.assertEqual(output.summary["actions_used"], 1)
        self.assertEqual(output.summary["direct_exposures"], 1)
        self.assertEqual(output.summary["new_adoptions"], 1)

    def test_referral_chain_advances_one_edge_per_tick(self):
        config = ModelConfig(
            n_consumers=4,
            network_type="ring",
            mean_degree=2,
            strategy="referral",
            market_sociality=0.0,
            seed_adopters=1,
            action_budget=3,
            actions_per_tick=1,
            horizon=3,
            beta_0=50.0,
        )
        model = EntrepreneurialNetworkActivationModel(
            config,
            graph=path_graph(4),
            consumers=consumers_for_test(4, {0}),
        )
        output = model.run()
        self.assertEqual(output.summary["new_adoptions"], 3)
        self.assertEqual(output.summary["max_cascade_depth"], 3)
        self.assertEqual([model.consumers[i].adoption_time for i in range(1, 4)], [1, 2, 3])

    def test_referrer_without_neighbor_starts_a_failed_attempt(self):
        graph = Graph.empty(3)
        graph.add_edge(1, 2)
        config = ModelConfig(
            n_consumers=3,
            network_type="ring",
            mean_degree=2,
            strategy="referral",
            seed_adopters=1,
            action_budget=5,
            actions_per_tick=1,
            horizon=2,
        )
        model = EntrepreneurialNetworkActivationModel(
            config,
            graph=graph,
            consumers=consumers_for_test(3, {0}),
        )
        output = model.run()
        self.assertEqual(output.summary["actions_used"], 2)
        self.assertEqual(output.summary["referral_exposures"], 0)
        self.assertEqual(output.summary["new_adoptions"], 0)
        self.assertEqual(output.summary["failed_attempts"], 2)
        self.assertEqual(output.summary["referrer_without_eligible_neighbor"], 2)

    def test_all_nonseed_adopters_were_aware_first(self):
        config = ModelConfig(master_seed=77)
        model = EntrepreneurialNetworkActivationModel(config)
        model.run()
        for consumer in model.consumers:
            if consumer.adopted and not consumer.is_seed:
                self.assertIsNotNone(consumer.awareness_time)
                self.assertLessEqual(consumer.awareness_time, consumer.adoption_time)

    def test_zero_seed_referral_is_valid_but_inactive(self):
        config = ModelConfig(
            n_consumers=3,
            network_type="custom",
            mean_degree=1,
            strategy="referral",
            seed_adopters=0,
            action_budget=5,
            horizon=2,
        )
        output = EntrepreneurialNetworkActivationModel(
            config,
            graph=complete_graph(3),
            consumers=consumers_for_test(3, set()),
        ).run()
        self.assertEqual(output.summary["actions_used"], 0)
        self.assertEqual(output.summary["new_adoptions"], 0)

    def test_equal_credibility_matched_target_is_label_invariant(self):
        base = ModelConfig(
            n_consumers=2,
            network_type="custom",
            mean_degree=1,
            seed_adopters=1,
            action_budget=1,
            actions_per_tick=1,
            horizon=1,
            market_sociality=0.8,
            direct_source_credibility=0.65,
            referral_source_credibility=0.65,
            master_seed=301,
        )
        graph = path_graph(2)
        population = consumers_for_test(2, {0})
        direct = EntrepreneurialNetworkActivationModel(
            base.with_updates(strategy="direct"),
            graph=graph,
            consumers=population,
        ).run()
        referral = EntrepreneurialNetworkActivationModel(
            base.with_updates(strategy="referral"),
            graph=graph,
            consumers=population,
        ).run()
        direct_eval = [e for e in direct.events if e["event_type"] == "evaluation"][0]
        referral_eval = [e for e in referral.events if e["event_type"] == "evaluation"][0]
        self.assertEqual(direct_eval["social_evidence"], referral_eval["social_evidence"])
        self.assertEqual(direct_eval["utility"], referral_eval["utility"])
        self.assertEqual(direct_eval["probability"], referral_eval["probability"])
        self.assertEqual(direct_eval["adopted"], referral_eval["adopted"])

    def test_high_credibility_reduces_more_uncertainty_than_low_credibility(self):
        base = ModelConfig(
            n_consumers=2,
            network_type="custom",
            mean_degree=1,
            strategy="referral",
            seed_adopters=1,
            action_budget=1,
            actions_per_tick=1,
            horizon=1,
            delta_information=0.5,
        )
        graph = path_graph(2)
        population = consumers_for_test(2, {0})
        low = EntrepreneurialNetworkActivationModel(
            base.with_updates(referral_source_credibility=0.1),
            graph=graph,
            consumers=population,
        ).run()
        high = EntrepreneurialNetworkActivationModel(
            base.with_updates(referral_source_credibility=0.9),
            graph=graph,
            consumers=population,
        ).run()
        low_exposure = [e for e in low.events if e["event_type"] == "exposure"][0]
        high_exposure = [e for e in high.events if e["event_type"] == "exposure"][0]
        self.assertLess(
            high_exposure["uncertainty_after"], low_exposure["uncertainty_after"]
        )

    def test_credibility_has_no_effect_when_information_reduction_is_zero(self):
        base = ModelConfig(
            n_consumers=2,
            network_type="custom",
            mean_degree=1,
            strategy="referral",
            seed_adopters=1,
            action_budget=1,
            actions_per_tick=1,
            horizon=1,
            delta_information=0.0,
        )
        graph = path_graph(2)
        population = consumers_for_test(2, {0})
        low = EntrepreneurialNetworkActivationModel(
            base.with_updates(referral_source_credibility=0.0),
            graph=graph,
            consumers=population,
        ).run()
        high = EntrepreneurialNetworkActivationModel(
            base.with_updates(referral_source_credibility=1.0),
            graph=graph,
            consumers=population,
        ).run()
        low_exposure = [e for e in low.events if e["event_type"] == "exposure"][0]
        high_exposure = [e for e in high.events if e["event_type"] == "exposure"][0]
        self.assertEqual(
            low_exposure["uncertainty_after"], high_exposure["uncertainty_after"]
        )

    def test_uncertainty_remains_bounded_after_repeated_exposure(self):
        config = ModelConfig(
            n_consumers=2,
            network_type="custom",
            mean_degree=1,
            strategy="direct",
            seed_adopters=1,
            action_budget=5,
            actions_per_tick=1,
            horizon=5,
            delta_information=1.0,
            direct_source_credibility=1.0,
            minimum_uncertainty=0.2,
            beta_0=-50.0,
        )
        model = EntrepreneurialNetworkActivationModel(
            config,
            graph=path_graph(2),
            consumers=consumers_for_test(2, {0}),
        )
        model.run()
        self.assertGreaterEqual(model.consumers[1].uncertainty, 0.2)
        self.assertLessEqual(model.consumers[1].uncertainty, 1.0)

    def test_isolated_network_blocks_referrals(self):
        graph = Graph.empty(4)
        config = ModelConfig(
            n_consumers=4,
            network_type="custom",
            mean_degree=1,
            strategy="referral",
            seed_adopters=1,
            horizon=3,
        )
        output = EntrepreneurialNetworkActivationModel(
            config,
            graph=graph,
            consumers=consumers_for_test(4, {0}),
        ).run()
        self.assertEqual(output.summary["referral_exposures"], 0)

    def test_complete_network_exposes_at_most_capacity_per_tick(self):
        config = ModelConfig(
            n_consumers=6,
            network_type="custom",
            mean_degree=1,
            strategy="referral",
            seed_adopters=2,
            action_budget=10,
            actions_per_tick=2,
            horizon=2,
            beta_0=50.0,
        )
        output = EntrepreneurialNetworkActivationModel(
            config,
            graph=complete_graph(6),
            consumers=consumers_for_test(6, {0, 1}),
        ).run()
        self.assertTrue(all(row["actions_this_tick"] <= 2 for row in output.ticks))

    def test_fragmented_network_contains_referral_reach(self):
        config = ModelConfig(
            n_consumers=6,
            network_type="custom",
            mean_degree=1,
            strategy="referral",
            seed_adopters=1,
            action_budget=10,
            actions_per_tick=2,
            horizon=5,
            beta_0=50.0,
        )
        output = EntrepreneurialNetworkActivationModel(
            config,
            graph=fragmented_graph(),
            consumers=consumers_for_test(6, {0}),
        ).run()
        self.assertEqual(output.summary["new_adoptions"], 2)
        self.assertLess(output.summary["actions_used"], 10)

    def test_extremely_scarce_actions_are_conserved(self):
        config = ModelConfig(action_budget=1, actions_per_tick=5, horizon=10)
        output = EntrepreneurialNetworkActivationModel(config).run()
        self.assertEqual(output.summary["actions_used"], 1)

    def test_relatively_abundant_actions_remain_bounded_by_population(self):
        config = ModelConfig(
            n_consumers=10,
            network_type="ring",
            mean_degree=2,
            strategy="direct",
            seed_adopters=1,
            action_budget=100,
            actions_per_tick=20,
            horizon=3,
            allow_repeated_direct_contact=False,
            beta_0=-50.0,
        )
        output = EntrepreneurialNetworkActivationModel(config).run()
        self.assertLessEqual(output.summary["direct_exposures"], 9)


if __name__ == "__main__":
    unittest.main()
