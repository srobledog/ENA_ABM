import unittest

from ena_abm.agents import Consumer
from ena_abm.config import ModelConfig
from ena_abm.decision import ParsimoniousDecisionRule


def consumer(fit=0.6, status=0.5, uncertainty=0.8):
    return Consumer(
        consumer_id=0,
        fit=fit,
        status_quo_satisfaction=status,
        uncertainty=uncertainty,
        initial_uncertainty=uncertainty,
    )


class DecisionRuleTests(unittest.TestCase):
    def test_social_evidence_has_no_effect_when_sociality_is_zero(self):
        config = ModelConfig(market_sociality=0.0)
        rule = ParsimoniousDecisionRule(config)
        low = rule.evaluate(consumer(), 0.0)
        high = rule.evaluate(consumer(), 1.0)
        self.assertAlmostEqual(low.utility, high.utility)

    def test_social_evidence_increases_utility_in_social_uncertain_market(self):
        config = ModelConfig(market_sociality=1.0)
        rule = ParsimoniousDecisionRule(config)
        low = rule.evaluate(consumer(), 0.0)
        high = rule.evaluate(consumer(), 1.0)
        self.assertGreater(high.utility, low.utility)

    def test_status_quo_satisfaction_reduces_utility(self):
        rule = ParsimoniousDecisionRule(ModelConfig(market_sociality=0.0))
        low_status = rule.evaluate(consumer(status=0.2), 0.5)
        high_status = rule.evaluate(consumer(status=0.9), 0.5)
        self.assertGreater(low_status.utility, high_status.utility)

    def test_uncertainty_changes_weight_between_evidence_sources(self):
        rule = ParsimoniousDecisionRule(ModelConfig(market_sociality=1.0))
        low_uncertainty = rule.evaluate(
            consumer(fit=0.4, status=0.6, uncertainty=0.1), 1.0
        )
        high_uncertainty = rule.evaluate(
            consumer(fit=0.4, status=0.6, uncertainty=0.9), 1.0
        )
        self.assertGreater(high_uncertainty.utility, low_uncertainty.utility)

    def test_market_sociality_near_one_makes_social_evidence_relevant(self):
        rule = ParsimoniousDecisionRule(ModelConfig(market_sociality=0.99))
        low = rule.evaluate(consumer(uncertainty=0.9), 0.0)
        high = rule.evaluate(consumer(uncertainty=0.9), 1.0)
        self.assertGreater(high.utility, low.utility)

    def test_high_status_quo_satisfaction_lowers_probability(self):
        rule = ParsimoniousDecisionRule(ModelConfig(market_sociality=0.2))
        low = rule.evaluate(consumer(status=0.05), 0.5)
        high = rule.evaluate(consumer(status=0.95), 0.5)
        self.assertGreater(low.probability, high.probability)

    def test_probability_is_bounded_under_extreme_coefficients(self):
        rule = ParsimoniousDecisionRule(
            ModelConfig(beta_0=1_000.0, beta_individual=1_000.0, beta_social=1_000.0)
        )
        evaluation = rule.evaluate(consumer(), 1.0)
        self.assertGreaterEqual(evaluation.probability, 0.0)
        self.assertLessEqual(evaluation.probability, 1.0)

    def test_removed_referral_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            ModelConfig.from_dict({"referral_weight": 0.70})

    def test_credibility_bounds_are_validated(self):
        with self.assertRaises(ValueError):
            ModelConfig(direct_source_credibility=1.1).validate()


if __name__ == "__main__":
    unittest.main()
