from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from .config import ModelConfig


class ConsumerState(str, Enum):
    UNAWARE = "unaware"
    AWARE = "aware"
    EVALUATING = "evaluating"
    ADOPTED = "adopted"


@dataclass
class Consumer:
    consumer_id: int
    fit: float
    status_quo_satisfaction: float
    uncertainty: float
    initial_uncertainty: float
    state: ConsumerState = ConsumerState.UNAWARE
    is_seed: bool = False
    awareness_time: int | None = None
    adoption_time: int | None = None
    last_evaluation_time: int | None = None
    previous_adopted_neighbor_count: int = 0
    acquisition_source: str | None = None
    referral_parent: int | None = None
    cascade_depth: int = 0

    @property
    def adopted(self) -> bool:
        return self.state == ConsumerState.ADOPTED


def _truncated_normal(
    rng: random.Random, mean: float, standard_deviation: float
) -> float:
    if standard_deviation == 0:
        return min(1.0, max(0.0, mean))
    for _ in range(10_000):
        value = rng.gauss(mean, standard_deviation)
        if 0.0 <= value <= 1.0:
            return value
    raise RuntimeError("truncated normal sampler failed to draw a bounded value")


def create_consumers(
    config: ModelConfig,
    attribute_rng: random.Random,
    seed_ids: set[int],
) -> list[Consumer]:
    consumers: list[Consumer] = []
    for consumer_id in range(config.n_consumers):
        uncertainty = attribute_rng.betavariate(
            config.uncertainty_alpha, config.uncertainty_beta
        )
        consumer = Consumer(
            consumer_id=consumer_id,
            fit=_truncated_normal(attribute_rng, config.fit_mean, config.fit_sd),
            status_quo_satisfaction=attribute_rng.betavariate(
                config.status_alpha, config.status_beta
            ),
            uncertainty=uncertainty,
            initial_uncertainty=uncertainty,
        )
        if consumer_id in seed_ids:
            consumer.state = ConsumerState.ADOPTED
            consumer.is_seed = True
            consumer.awareness_time = 0
            consumer.adoption_time = 0
            consumer.acquisition_source = "seed"
        consumers.append(consumer)
    return consumers
