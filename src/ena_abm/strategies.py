from __future__ import annotations

import random
from abc import ABC, abstractmethod

from .agents import Consumer, ConsumerState
from .events import ActivationAttempt
from .network import Graph


class Strategy(ABC):
    @abstractmethod
    def select_attempts(
        self,
        graph: Graph,
        consumers: list[Consumer],
        capacity: int,
        tick: int,
        rng: random.Random,
    ) -> list[ActivationAttempt]:
        """Return feasible attempt starts, not successful exposures."""
        raise NotImplementedError


class DirectOutreachStrategy(Strategy):
    def __init__(self, allow_repeated_contact: bool = True):
        self.allow_repeated_contact = allow_repeated_contact
        self.contacted: set[int] = set()

    def select_attempts(
        self,
        graph: Graph,
        consumers: list[Consumer],
        capacity: int,
        tick: int,
        rng: random.Random,
    ) -> list[ActivationAttempt]:
        del graph
        non_adopters = [c for c in consumers if not c.adopted]
        priority = [
            c.consumer_id
            for c in non_adopters
            if c.state == ConsumerState.UNAWARE and c.consumer_id not in self.contacted
        ]
        secondary = [
            c.consumer_id
            for c in non_adopters
            if c.consumer_id not in self.contacted and c.consumer_id not in priority
        ]
        rng.shuffle(priority)
        rng.shuffle(secondary)
        candidates = priority + secondary
        if not candidates and self.allow_repeated_contact:
            candidates = [c.consumer_id for c in non_adopters]
            rng.shuffle(candidates)
        selected = candidates[:capacity]
        self.contacted.update(selected)
        return [
            ActivationAttempt(
                tick=tick,
                kind="direct",
                source_id=None,
                target_id=target,
            )
            for target in selected
        ]


class ReferralStrategy(Strategy):
    def select_attempts(
        self,
        graph: Graph,
        consumers: list[Consumer],
        capacity: int,
        tick: int,
        rng: random.Random,
    ) -> list[ActivationAttempt]:
        del graph
        # An adopted customer is a feasible person from whom to request a
        # referral. Whether that person accepts and can identify an eligible
        # neighbor belongs to later stages of the exposure process.
        sources = [c.consumer_id for c in consumers if c.adopted]
        rng.shuffle(sources)
        return [
            ActivationAttempt(
                tick=tick,
                kind="referral",
                source_id=source,
                target_id=None,
            )
            for source in sources[:capacity]
        ]


def make_strategy(name: str, allow_repeated_direct_contact: bool) -> Strategy:
    if name == "direct":
        return DirectOutreachStrategy(allow_repeated_direct_contact)
    if name == "referral":
        return ReferralStrategy()
    raise ValueError(f"unknown strategy: {name}")
