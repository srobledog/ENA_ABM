from __future__ import annotations

import math
from dataclasses import dataclass

from .agents import Consumer
from .config import ModelConfig


@dataclass(frozen=True)
class DecisionEvaluation:
    utility: float
    probability: float
    social_reliance: float
    individual_evaluation: float
    social_evidence: float


class ParsimoniousDecisionRule:
    """Label-invariant v0.3 adoption rule.

    The rule receives observed network behavior, not an exposure-type signal.
    Source credibility acts upstream through the uncertainty update.
    """

    def __init__(self, config: ModelConfig):
        self.config = config

    @staticmethod
    def _bounded(value: float) -> float:
        return min(1.0, max(0.0, value))

    @staticmethod
    def _logistic(value: float) -> float:
        if value >= 0:
            z = math.exp(-value)
            return 1.0 / (1.0 + z)
        z = math.exp(value)
        return z / (1.0 + z)

    def evaluate(self, consumer: Consumer, social_evidence: float) -> DecisionEvaluation:
        social_evidence = self._bounded(social_evidence)
        social_reliance = self._bounded(
            self.config.market_sociality * consumer.uncertainty
        )
        individual_evaluation = consumer.fit - consumer.status_quo_satisfaction
        utility = (
            self.config.beta_0
            + self.config.beta_individual
            * (1.0 - social_reliance)
            * individual_evaluation
            + self.config.beta_social
            * social_reliance
            * (2.0 * social_evidence - 1.0)
        )
        return DecisionEvaluation(
            utility=utility,
            probability=self._logistic(utility),
            social_reliance=social_reliance,
            individual_evaluation=individual_evaluation,
            social_evidence=social_evidence,
        )
