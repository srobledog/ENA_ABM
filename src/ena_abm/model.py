from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .agents import Consumer, ConsumerState, create_consumers
from .config import ModelConfig
from .decision import ParsimoniousDecisionRule
from .events import ActivationAttempt, ExposureEvent, PendingAdoption
from .network import Graph, generate_network
from .rng import random_stream, stable_seed
from .strategies import make_strategy


@dataclass
class SimulationOutput:
    summary: dict[str, Any]
    ticks: list[dict[str, Any]]
    events: list[dict[str, Any]]
    initialization_signature: str


class EntrepreneurialNetworkActivationModel:
    """ENA ABM v0.4 with explicit attempt, exposure, and adoption stages."""

    def __init__(
        self,
        config: ModelConfig,
        *,
        graph: Graph | None = None,
        consumers: list[Consumer] | None = None,
    ):
        config.validate()
        self.config = config
        self.network_seed = stable_seed(
            config.master_seed, "network", config.network_type, config.replicate_id
        )
        self.attribute_seed = stable_seed(
            config.master_seed, "attributes", config.network_type, config.replicate_id
        )
        self.seed_selection_seed = stable_seed(
            config.master_seed, "seed_adopters", config.network_type, config.replicate_id
        )
        self.strategy_seed = stable_seed(
            config.master_seed, "strategy_events", config.network_type, config.replicate_id
        )
        self.exposure_process_seed = stable_seed(
            config.master_seed, "exposure_process", config.network_type, config.replicate_id
        )
        self.decision_seed = stable_seed(
            config.master_seed, "decision_events", config.network_type, config.replicate_id
        )

        if graph is None:
            self.graph = generate_network(
                config.network_type,
                config.n_consumers,
                config.mean_degree,
                config.rewire_probability,
                random_stream(self.network_seed, "generator"),
            )
        else:
            self.graph = graph.copy()
        self.graph.validate()
        if self.graph.n != config.n_consumers:
            raise ValueError("graph size and n_consumers do not match")

        if consumers is None:
            seed_rng = random_stream(self.seed_selection_seed, "selection")
            seed_ids = set(
                seed_rng.sample(range(config.n_consumers), config.seed_adopters)
            )
            self.consumers = create_consumers(
                config,
                random_stream(self.attribute_seed, "consumer_factory"),
                seed_ids,
            )
        else:
            if len(consumers) != config.n_consumers:
                raise ValueError("consumer count and n_consumers do not match")
            self.consumers = copy.deepcopy(consumers)
            seed_ids = {c.consumer_id for c in self.consumers if c.is_seed}
            if len(seed_ids) != config.seed_adopters:
                raise ValueError("custom consumers must match config.seed_adopters")

        self.seed_ids = seed_ids
        self.strategy_rng = random_stream(self.strategy_seed, "selection")
        self.exposure_rng = random_stream(self.exposure_process_seed, "stage_outcomes")
        self.decision_rng = random_stream(self.decision_seed, "adoption")
        self.strategy = make_strategy(
            config.strategy, config.allow_repeated_direct_contact
        )
        self.decision_rule = ParsimoniousDecisionRule(config)
        self.tick = 0
        self.attempts_started = 0
        self.failed_attempts = 0
        self.requests_accepted = 0
        self.exposures_delivered = 0
        self.actions_used = 0
        self.cost_spent = 0.0
        self.cost_by_stage: dict[str, float] = {}
        self.eligible_sources_seen = 0
        self.eligible_neighbors_found = 0
        self.unavailable_opportunities = 0
        self.direct_contact_failures = 0
        self.referral_rejections = 0
        self.referrer_without_eligible_neighbor = 0
        self.referral_introduction_failures = 0
        self.stage_resource_failures = 0
        self.unfunded_followups = 0
        self.evaluated_consumers: set[int] = set()
        self.tick_records: list[dict[str, Any]] = []
        self.event_records: list[dict[str, Any]] = []
        self.time_to_takeoff: int | None = None
        self.initialization_signature = self._initialization_signature()

    def _initialization_signature(self) -> str:
        payload = {
            "edges": self.graph.edges(),
            "consumers": [
                {
                    "id": c.consumer_id,
                    "fit": c.fit,
                    "status": c.status_quo_satisfaction,
                    "uncertainty": c.initial_uncertainty,
                    "seed": c.is_seed,
                }
                for c in self.consumers
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        return hashlib.sha256(encoded).hexdigest()

    def _adopted_snapshot(self) -> list[bool]:
        return [consumer.adopted for consumer in self.consumers]

    def _neighbor_adoption_counts(self, adopted_snapshot: list[bool]) -> list[int]:
        return [
            sum(1 for neighbor in self.graph.neighbors(node) if adopted_snapshot[neighbor])
            for node in range(self.graph.n)
        ]

    def _action_cost(self) -> float:
        return (
            self.config.direct_action_cost
            if self.config.strategy == "direct"
            else self.config.referral_action_cost
        )

    def _source_credibility(self, event: ExposureEvent) -> float:
        return (
            self.config.direct_source_credibility
            if event.kind == "direct"
            else self.config.referral_source_credibility
        )

    def _remaining_budget(self) -> float:
        return max(0.0, self.config.budget_limit - self.cost_spent)

    def _can_spend(self, amount: float) -> bool:
        if self.config.fairness_criterion != "equal_budget":
            return True
        return amount <= self._remaining_budget() + 1e-12

    def _start_cost(self) -> float:
        cost = self._action_cost()
        if self.config.cost_accounting == "upfront_expected":
            return cost
        if self.config.strategy == "direct":
            return cost * (
                self.config.direct_search_share
                + self.config.direct_contact_share
                + self.config.direct_coordination_share
            )
        return cost * (
            self.config.referral_identify_share
            + self.config.referral_request_share
        )

    def _available_attempt_slots(self) -> int:
        capacity = self.config.actions_per_tick
        if self.config.fairness_criterion == "equal_actions":
            return max(0, min(capacity, self.config.action_budget - self.actions_used))
        if self.config.fairness_criterion == "equal_budget":
            if not self._can_spend(self._start_cost()):
                return 0
            # Staged costs are charged sequentially, so affordability is checked
            # again before every attempt and conditional stage.
            return capacity
        remaining_exposures = self.config.exposure_quota - self.exposures_delivered
        return capacity if remaining_exposures > 0 else 0

    def _resource_limit_reached(self) -> bool:
        if self.config.fairness_criterion == "equal_actions":
            return self.actions_used >= self.config.action_budget
        if self.config.fairness_criterion == "equal_budget":
            return not self._can_spend(self._start_cost())
        return self.exposures_delivered >= self.config.exposure_quota

    def _empty_event_row(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "event_type": "",
            "exposure_kind": "",
            "attempt_id": "",
            "attempt_outcome": "",
            "cost_stage": "",
            "source_id": "",
            "target_id": "",
            "cost_increment": "",
            "cumulative_cost": self.cost_spent,
            "accepted": "",
            "eligible_neighbor": "",
            "effective_exposure": "",
            "source_credibility": "",
            "uncertainty_before": "",
            "uncertainty_after": "",
            "probability": "",
            "utility": "",
            "social_evidence": "",
            "social_reliance": "",
            "individual_evaluation": "",
            "adopted": "",
        }

    def _charge(
        self,
        amount: float,
        *,
        stage: str,
        attempt_id: int,
        attempt: ActivationAttempt,
        target_id: int | None = None,
    ) -> bool:
        if amount <= 1e-15:
            return True
        if not self._can_spend(amount):
            return False
        self.cost_spent += amount
        if (
            self.config.fairness_criterion == "equal_budget"
            and self.cost_spent > self.config.budget_limit + 1e-9
        ):
            raise AssertionError("budget became negative")
        self.cost_by_stage[stage] = self.cost_by_stage.get(stage, 0.0) + amount
        row = self._empty_event_row()
        row.update(
            {
                "event_type": "cost",
                "exposure_kind": attempt.kind,
                "attempt_id": attempt_id,
                "cost_stage": stage,
                "source_id": "" if attempt.source_id is None else attempt.source_id,
                "target_id": (
                    ""
                    if (target_id is None and attempt.target_id is None)
                    else (attempt.target_id if target_id is None else target_id)
                ),
                "cost_increment": amount,
                "cumulative_cost": self.cost_spent,
            }
        )
        self.event_records.append(row)
        return True

    def _charge_attempt_start(
        self, attempt: ActivationAttempt, attempt_id: int
    ) -> bool:
        cost = self._action_cost()
        if self.config.cost_accounting == "upfront_expected":
            return self._charge(
                cost,
                stage="attempt_total_expected",
                attempt_id=attempt_id,
                attempt=attempt,
            )
        if attempt.kind == "direct":
            stages = [
                ("direct_search", self.config.direct_search_share),
                ("direct_contact", self.config.direct_contact_share),
                ("direct_coordination", self.config.direct_coordination_share),
            ]
        else:
            stages = [
                ("referral_identify", self.config.referral_identify_share),
                ("referral_request", self.config.referral_request_share),
            ]
        required = cost * sum(share for _, share in stages)
        if not self._can_spend(required):
            return False
        for stage, share in stages:
            if not self._charge(
                cost * share,
                stage=stage,
                attempt_id=attempt_id,
                attempt=attempt,
            ):
                raise AssertionError("prechecked start-stage cost was not affordable")
        return True

    def _charge_referral_coordination(
        self, attempt: ActivationAttempt, attempt_id: int
    ) -> bool:
        if self.config.cost_accounting == "upfront_expected":
            return True
        return self._charge(
            self._action_cost() * self.config.referral_coordination_share,
            stage="referral_coordination",
            attempt_id=attempt_id,
            attempt=attempt,
        )

    def _charge_followup(
        self,
        attempt: ActivationAttempt,
        attempt_id: int,
        target_id: int,
    ) -> bool:
        if self.config.cost_accounting == "upfront_expected":
            return True
        share = (
            self.config.direct_followup_share
            if attempt.kind == "direct"
            else self.config.referral_followup_share
        )
        stage = (
            "direct_followup"
            if attempt.kind == "direct"
            else "referral_followup"
        )
        return self._charge(
            self._action_cost() * share,
            stage=stage,
            attempt_id=attempt_id,
            attempt=attempt,
            target_id=target_id,
        )

    def _record_attempt(
        self,
        attempt: ActivationAttempt,
        *,
        attempt_id: int,
        outcome: str,
        cost_before: float,
        accepted: bool | None,
        eligible_neighbor: bool | None,
        effective_exposure: bool,
        target_id: int | None,
    ) -> None:
        row = self._empty_event_row()
        row.update(
            {
                "event_type": "attempt",
                "exposure_kind": attempt.kind,
                "attempt_id": attempt_id,
                "attempt_outcome": outcome,
                "source_id": "" if attempt.source_id is None else attempt.source_id,
                "target_id": (
                    ""
                    if (target_id is None and attempt.target_id is None)
                    else (attempt.target_id if target_id is None else target_id)
                ),
                "cost_increment": self.cost_spent - cost_before,
                "cumulative_cost": self.cost_spent,
                "accepted": "" if accepted is None else int(accepted),
                "eligible_neighbor": (
                    "" if eligible_neighbor is None else int(eligible_neighbor)
                ),
                "effective_exposure": int(effective_exposure),
            }
        )
        self.event_records.append(row)

    def _process_attempt(
        self,
        attempt: ActivationAttempt,
        *,
        selected_exposure_targets: set[int],
    ) -> ExposureEvent | None:
        attempt_id = self.attempts_started + 1
        cost_before = self.cost_spent
        if not self._charge_attempt_start(attempt, attempt_id):
            return None
        self.attempts_started += 1
        self.actions_used += 1

        if attempt.kind == "direct":
            if attempt.target_id is None:
                raise AssertionError("direct attempt lacks a target")
            exposed = (
                self.exposure_rng.random()
                < self.config.direct_exposure_probability
            )
            if not exposed:
                self.failed_attempts += 1
                self.direct_contact_failures += 1
                self._record_attempt(
                    attempt,
                    attempt_id=attempt_id,
                    outcome="direct_exposure_failed",
                    cost_before=cost_before,
                    accepted=None,
                    eligible_neighbor=None,
                    effective_exposure=False,
                    target_id=attempt.target_id,
                )
                return None
            if not self._charge_followup(
                attempt, attempt_id, attempt.target_id
            ):
                self.unfunded_followups += 1
            self._record_attempt(
                attempt,
                attempt_id=attempt_id,
                outcome="effective_exposure",
                cost_before=cost_before,
                accepted=None,
                eligible_neighbor=None,
                effective_exposure=True,
                target_id=attempt.target_id,
            )
            return ExposureEvent(
                tick=self.tick,
                kind="direct",
                source_id=None,
                target_id=attempt.target_id,
                attempt_id=attempt_id,
            )

        if attempt.source_id is None:
            raise AssertionError("referral attempt lacks a source")
        accepted = (
            self.exposure_rng.random()
            < self.config.referral_acceptance_probability
        )
        if not accepted:
            self.failed_attempts += 1
            self.referral_rejections += 1
            self._record_attempt(
                attempt,
                attempt_id=attempt_id,
                outcome="referral_rejected",
                cost_before=cost_before,
                accepted=False,
                eligible_neighbor=None,
                effective_exposure=False,
                target_id=None,
            )
            return None
        self.requests_accepted += 1

        if not self._charge_referral_coordination(attempt, attempt_id):
            self.failed_attempts += 1
            self.stage_resource_failures += 1
            self._record_attempt(
                attempt,
                attempt_id=attempt_id,
                outcome="coordination_unfunded",
                cost_before=cost_before,
                accepted=True,
                eligible_neighbor=None,
                effective_exposure=False,
                target_id=None,
            )
            return None

        candidates = [
            target
            for target in self.graph.neighbors(attempt.source_id)
            if not self.consumers[target].adopted
            and target not in selected_exposure_targets
        ]
        if not candidates:
            self.failed_attempts += 1
            self.referrer_without_eligible_neighbor += 1
            self._record_attempt(
                attempt,
                attempt_id=attempt_id,
                outcome="no_structural_eligible_neighbor",
                cost_before=cost_before,
                accepted=True,
                eligible_neighbor=False,
                effective_exposure=False,
                target_id=None,
            )
            return None
        neighbor_available = (
            self.exposure_rng.random()
            < self.config.referral_neighbor_availability_probability
        )
        if not neighbor_available:
            self.failed_attempts += 1
            self.referrer_without_eligible_neighbor += 1
            self._record_attempt(
                attempt,
                attempt_id=attempt_id,
                outcome="eligible_neighbor_unavailable",
                cost_before=cost_before,
                accepted=True,
                eligible_neighbor=False,
                effective_exposure=False,
                target_id=None,
            )
            return None
        self.eligible_neighbors_found += 1
        target_id = self.strategy_rng.choice(candidates)
        introduced = (
            self.exposure_rng.random()
            < self.config.referral_introduction_probability
        )
        if not introduced:
            self.failed_attempts += 1
            self.referral_introduction_failures += 1
            self._record_attempt(
                attempt,
                attempt_id=attempt_id,
                outcome="introduction_failed",
                cost_before=cost_before,
                accepted=True,
                eligible_neighbor=True,
                effective_exposure=False,
                target_id=target_id,
            )
            return None
        if not self._charge_followup(attempt, attempt_id, target_id):
            self.unfunded_followups += 1
        self._record_attempt(
            attempt,
            attempt_id=attempt_id,
            outcome="effective_exposure",
            cost_before=cost_before,
            accepted=True,
            eligible_neighbor=True,
            effective_exposure=True,
            target_id=target_id,
        )
        return ExposureEvent(
            tick=self.tick,
            kind="referral",
            source_id=attempt.source_id,
            target_id=target_id,
            attempt_id=attempt_id,
        )

    def _record_exposure(
        self,
        event: ExposureEvent,
        *,
        source_credibility: float,
        uncertainty_before: float,
        uncertainty_after: float,
    ) -> None:
        row = self._empty_event_row()
        row.update(
            {
                "event_type": "exposure",
                "exposure_kind": event.kind,
                "attempt_id": event.attempt_id,
                "source_id": "" if event.source_id is None else event.source_id,
                "target_id": event.target_id,
                "effective_exposure": 1,
                "source_credibility": source_credibility,
                "uncertainty_before": uncertainty_before,
                "uncertainty_after": uncertainty_after,
            }
        )
        self.event_records.append(row)

    def _record_evaluation(
        self,
        pending: PendingAdoption,
        adopted: bool,
    ) -> None:
        row = self._empty_event_row()
        row.update(
            {
                "event_type": "evaluation",
                "exposure_kind": pending.exposure_kind or "organic_social",
                "attempt_id": "" if pending.attempt_id is None else pending.attempt_id,
                "source_id": "" if pending.source_id is None else pending.source_id,
                "target_id": pending.consumer_id,
                "source_credibility": (
                    "" if pending.source_credibility is None else pending.source_credibility
                ),
                "probability": pending.probability,
                "utility": pending.utility,
                "social_evidence": pending.social_evidence,
                "social_reliance": pending.social_reliance,
                "individual_evaluation": pending.individual_evaluation,
                "adopted": int(adopted),
            }
        )
        self.event_records.append(row)

    def step(self) -> None:
        self.tick += 1
        adopted_snapshot = self._adopted_snapshot()
        neighbor_counts = self._neighbor_adoption_counts(adopted_snapshot)
        attempts_before = self.attempts_started
        failures_before = self.failed_attempts
        accepted_before = self.requests_accepted
        exposures_before = self.exposures_delivered
        cost_before_tick = self.cost_spent
        unavailable_before = self.unavailable_opportunities

        available = self._available_attempt_slots()
        if self.config.strategy == "referral":
            self.eligible_sources_seen += sum(adopted_snapshot)
        attempts = (
            self.strategy.select_attempts(
                self.graph,
                self.consumers,
                available,
                self.tick,
                self.strategy_rng,
            )
            if available > 0
            else []
        )
        if len(attempts) > available:
            raise AssertionError("strategy exceeded available attempt slots")
        if available > 0 and not attempts:
            self.unavailable_opportunities += 1

        events: list[ExposureEvent] = []
        selected_exposure_targets: set[int] = set()
        for attempt in attempts:
            if not self._can_spend(self._start_cost()):
                break
            if (
                self.config.fairness_criterion == "equal_exposures"
                and self.exposures_delivered + len(events) >= self.config.exposure_quota
            ):
                break
            event = self._process_attempt(
                attempt,
                selected_exposure_targets=selected_exposure_targets,
            )
            if event is not None:
                if event.target_id in selected_exposure_targets:
                    raise AssertionError(
                        "a target received multiple entrepreneurial exposures in one tick"
                    )
                selected_exposure_targets.add(event.target_id)
                events.append(event)

        self.exposures_delivered += len(events)
        exposure_by_target = {event.target_id: event for event in events}

        for event in events:
            consumer = self.consumers[event.target_id]
            if consumer.adopted:
                raise AssertionError("strategy exposed an already adopted consumer")
            if consumer.state == ConsumerState.UNAWARE:
                consumer.state = ConsumerState.AWARE
                consumer.awareness_time = self.tick
            consumer.state = ConsumerState.EVALUATING
            credibility = self._source_credibility(event)
            uncertainty_before = consumer.uncertainty
            consumer.uncertainty = max(
                self.config.minimum_uncertainty,
                consumer.uncertainty
                * (1.0 - self.config.delta_information * credibility),
            )
            self._record_exposure(
                event,
                source_credibility=credibility,
                uncertainty_before=uncertainty_before,
                uncertainty_after=consumer.uncertainty,
            )

        triggered: list[int] = []
        for consumer in self.consumers:
            if consumer.adopted or consumer.state == ConsumerState.UNAWARE:
                continue
            exposed = consumer.consumer_id in exposure_by_target
            social_change = (
                consumer.last_evaluation_time is not None
                and neighbor_counts[consumer.consumer_id]
                != consumer.previous_adopted_neighbor_count
            )
            if exposed or social_change:
                consumer.state = ConsumerState.EVALUATING
                triggered.append(consumer.consumer_id)
                self.evaluated_consumers.add(consumer.consumer_id)

        pending_adoptions: list[PendingAdoption] = []
        for consumer_id in sorted(triggered):
            consumer = self.consumers[consumer_id]
            degree = self.graph.degree(consumer_id)
            neighborhood_share = (
                neighbor_counts[consumer_id] / degree if degree else 0.0
            )
            event = exposure_by_target.get(consumer_id)
            social_evidence = min(1.0, max(0.0, neighborhood_share))
            evaluation = self.decision_rule.evaluate(consumer, social_evidence)
            pending_adoptions.append(
                PendingAdoption(
                    consumer_id=consumer_id,
                    probability=evaluation.probability,
                    utility=evaluation.utility,
                    social_evidence=evaluation.social_evidence,
                    social_reliance=evaluation.social_reliance,
                    individual_evaluation=evaluation.individual_evaluation,
                    source_credibility=(
                        None if event is None else self._source_credibility(event)
                    ),
                    exposure_kind=None if event is None else event.kind,
                    source_id=None if event is None else event.source_id,
                    attempt_id=None if event is None else event.attempt_id,
                )
            )
            consumer.last_evaluation_time = self.tick
            consumer.previous_adopted_neighbor_count = neighbor_counts[consumer_id]

        adopted_this_tick: list[int] = []
        for pending in pending_adoptions:
            adopted = self.decision_rng.random() < pending.probability
            self._record_evaluation(pending, adopted)
            consumer = self.consumers[pending.consumer_id]
            if adopted:
                adopted_this_tick.append(pending.consumer_id)
            else:
                consumer.state = ConsumerState.AWARE

        adopted_set = set(adopted_this_tick)
        for pending in pending_adoptions:
            if pending.consumer_id not in adopted_set:
                continue
            consumer = self.consumers[pending.consumer_id]
            if consumer.state == ConsumerState.UNAWARE:
                raise AssertionError("adoption without awareness")
            consumer.state = ConsumerState.ADOPTED
            consumer.adoption_time = self.tick
            if pending.exposure_kind == "referral" and pending.source_id is not None:
                consumer.acquisition_source = "referral"
                consumer.referral_parent = pending.source_id
                consumer.cascade_depth = (
                    self.consumers[pending.source_id].cascade_depth + 1
                )
            elif pending.exposure_kind == "direct":
                consumer.acquisition_source = "direct"
                consumer.cascade_depth = 0
            else:
                consumer.acquisition_source = "organic_social"
                consumer.cascade_depth = 0

        new_adoptions = sum(
            1 for consumer in self.consumers if consumer.adopted and not consumer.is_seed
        )
        threshold = math.ceil(
            self.config.takeoff_share
            * (self.config.n_consumers - self.config.seed_adopters)
        )
        if self.time_to_takeoff is None and new_adoptions >= threshold:
            self.time_to_takeoff = self.tick

        if (
            self.config.fairness_criterion == "equal_budget"
            and self.cost_spent > self.config.budget_limit + 1e-9
        ):
            raise AssertionError("budget conservation failed")
        self.tick_records.append(
            {
                "tick": self.tick,
                "eligible_sources": (
                    sum(adopted_snapshot)
                    if self.config.strategy == "referral"
                    else 0
                ),
                "attempts_this_tick": self.attempts_started - attempts_before,
                "attempts_started": self.attempts_started,
                "failed_attempts_this_tick": self.failed_attempts - failures_before,
                "failed_attempts": self.failed_attempts,
                "accepted_requests_this_tick": (
                    self.requests_accepted - accepted_before
                ),
                "accepted_requests": self.requests_accepted,
                "unavailable_opportunities_this_tick": (
                    self.unavailable_opportunities - unavailable_before
                ),
                "unavailable_opportunities": self.unavailable_opportunities,
                "actions_this_tick": self.attempts_started - attempts_before,
                "actions_used": self.actions_used,
                "cost_this_tick": self.cost_spent - cost_before_tick,
                "cost_spent": self.cost_spent,
                "exposures_this_tick": self.exposures_delivered - exposures_before,
                "exposures_delivered": self.exposures_delivered,
                "direct_exposures": sum(event.kind == "direct" for event in events),
                "referral_exposures": sum(event.kind == "referral" for event in events),
                "evaluations": len(triggered),
                "new_adoptions_this_tick": len(adopted_this_tick),
                "cumulative_new_adoptions": new_adoptions,
                "total_adopters": new_adoptions + len(self.seed_ids),
                "aware_nonadopters": sum(
                    consumer.state in {ConsumerState.AWARE, ConsumerState.EVALUATING}
                    for consumer in self.consumers
                ),
                "unused_budget": self._remaining_budget(),
                "mean_uncertainty_nonadopters": self._mean_uncertainty_nonadopters(),
            }
        )

    def _mean_uncertainty_nonadopters(self) -> float:
        values = [c.uncertainty for c in self.consumers if not c.adopted]
        return sum(values) / len(values) if values else 0.0

    def run(self) -> SimulationOutput:
        while self.tick < self.config.horizon:
            self.step()
        return SimulationOutput(
            summary=self._summary(),
            ticks=copy.deepcopy(self.tick_records),
            events=copy.deepcopy(self.event_records),
            initialization_signature=self.initialization_signature,
        )

    def _largest_referral_cascade(self) -> int:
        children: dict[int, list[int]] = {}
        for consumer in self.consumers:
            if (
                consumer.acquisition_source == "referral"
                and consumer.referral_parent is not None
            ):
                children.setdefault(consumer.referral_parent, []).append(
                    consumer.consumer_id
                )

        def descendants(node: int) -> int:
            return sum(1 + descendants(child) for child in children.get(node, []))

        return max((descendants(seed) for seed in self.seed_ids), default=0)

    def _summary(self) -> dict[str, Any]:
        new_adopters = [
            consumer
            for consumer in self.consumers
            if consumer.adopted and not consumer.is_seed
        ]
        non_seed_count = self.config.n_consumers - self.config.seed_adopters
        unique_aware = sum(
            consumer.awareness_time is not None and not consumer.is_seed
            for consumer in self.consumers
        )
        final_quiet = self.tick_records[-self.config.quiet_period :]
        takeoff = self.time_to_takeoff is not None
        entrepreneurial_actions_ended = (
            self._resource_limit_reached()
            or all(record["attempts_this_tick"] == 0 for record in final_quiet)
        )
        extinction = (
            not takeoff
            and entrepreneurial_actions_ended
            and all(record["new_adoptions_this_tick"] == 0 for record in final_quiet)
        )
        adoption_times = [
            c.adoption_time for c in new_adopters if c.adoption_time is not None
        ]
        unused_budget = self._remaining_budget()
        cost_per_attempt = (
            self.cost_spent / self.attempts_started if self.attempts_started else ""
        )
        cost_per_exposure = (
            self.cost_spent / self.exposures_delivered
            if self.exposures_delivered
            else ""
        )
        cost_per_adoption = (
            self.cost_spent / len(new_adopters) if new_adopters else ""
        )
        summary: dict[str, Any] = {
            "scenario_id": (
                f"{self.config.network_type}|sociality={self.config.market_sociality:.2f}|"
                f"{self.config.strategy}|accounting={self.config.cost_accounting}|"
                f"replicate={self.config.replicate_id}"
            ),
            "model_version": "0.4.0",
            "replicate_id": self.config.replicate_id,
            "strategy": self.config.strategy,
            "fairness_criterion": self.config.fairness_criterion,
            "cost_accounting": self.config.cost_accounting,
            "network_type": self.config.network_type,
            "market_sociality": self.config.market_sociality,
            "master_seed": self.config.master_seed,
            "network_seed": self.network_seed,
            "attribute_seed": self.attribute_seed,
            "seed_selection_seed": self.seed_selection_seed,
            "strategy_seed": self.strategy_seed,
            "exposure_process_seed": self.exposure_process_seed,
            "decision_seed": self.decision_seed,
            "initialization_signature": self.initialization_signature,
            "n_consumers": self.config.n_consumers,
            "seed_adopters": self.config.seed_adopters,
            "direct_action_cost": self.config.direct_action_cost,
            "referral_action_cost": self.config.referral_action_cost,
            "relative_referral_cost": (
                self.config.referral_action_cost / self.config.direct_action_cost
            ),
            "direct_exposure_probability": self.config.direct_exposure_probability,
            "referral_acceptance_probability": (
                self.config.referral_acceptance_probability
            ),
            "referral_neighbor_availability_probability": (
                self.config.referral_neighbor_availability_probability
            ),
            "referral_introduction_probability": (
                self.config.referral_introduction_probability
            ),
            "eligible_sources_seen": self.eligible_sources_seen,
            "eligible_neighbors_found": self.eligible_neighbors_found,
            "unavailable_opportunities": self.unavailable_opportunities,
            "attempts_started": self.attempts_started,
            "failed_attempts": self.failed_attempts,
            "requests_accepted": self.requests_accepted,
            "direct_contact_failures": self.direct_contact_failures,
            "referral_rejections": self.referral_rejections,
            "referrer_without_eligible_neighbor": (
                self.referrer_without_eligible_neighbor
            ),
            "referral_introduction_failures": (
                self.referral_introduction_failures
            ),
            "stage_resource_failures": self.stage_resource_failures,
            "unfunded_followups": self.unfunded_followups,
            "exposures_delivered": self.exposures_delivered,
            "direct_exposures": sum(
                record["direct_exposures"] for record in self.tick_records
            ),
            "referral_exposures": sum(
                record["referral_exposures"] for record in self.tick_records
            ),
            "evaluation_events": sum(
                record["evaluations"] for record in self.tick_records
            ),
            "unique_consumers_evaluated": len(self.evaluated_consumers),
            "new_adoptions": len(new_adopters),
            "strategy_generated_adoptions": len(new_adopters),
            "adoption_rate_nonseed": len(new_adopters) / non_seed_count,
            "direct_adoptions": sum(
                c.acquisition_source == "direct" for c in new_adopters
            ),
            "referral_adoptions": sum(
                c.acquisition_source == "referral" for c in new_adopters
            ),
            "organic_social_adoptions": sum(
                c.acquisition_source == "organic_social" for c in new_adopters
            ),
            "unique_aware_nonseed": unique_aware,
            "awareness_rate_nonseed": unique_aware / non_seed_count,
            "actions_used": self.actions_used,
            "action_limit": self.config.action_budget,
            "cost_spent": self.cost_spent,
            "budget_limit": self.config.budget_limit,
            "unused_actions": max(0, self.config.action_budget - self.actions_used),
            "unused_budget": unused_budget,
            "unused_exposure_quota": max(
                0, self.config.exposure_quota - self.exposures_delivered
            ),
            "budget_conservation_error": (
                self.config.budget_limit - self.cost_spent - unused_budget
            ),
            "full_attempt_cost_equivalent": (
                self.attempts_started * self._action_cost()
            ),
            "cost_per_attempt": cost_per_attempt,
            "cost_per_effective_exposure": cost_per_exposure,
            "cost_per_new_adopter": cost_per_adoption,
            "exposures_per_attempt": (
                self.exposures_delivered / self.attempts_started
                if self.attempts_started
                else 0.0
            ),
            "adoptions_per_exposure": (
                len(new_adopters) / self.exposures_delivered
                if self.exposures_delivered
                else 0.0
            ),
            "adoptions_per_action": (
                len(new_adopters) / self.attempts_started
                if self.attempts_started
                else 0.0
            ),
            "adoptions_per_budget_unit": (
                len(new_adopters) / self.cost_spent if self.cost_spent else 0.0
            ),
            "adoptions_per_allocated_budget_unit": (
                len(new_adopters) / self.config.budget_limit
                if self.config.budget_limit
                else 0.0
            ),
            "time_to_first_new_adoption": (
                min(adoption_times) if adoption_times else ""
            ),
            "mean_time_to_adoption": (
                sum(adoption_times) / len(adoption_times) if adoption_times else ""
            ),
            "time_to_takeoff": (
                self.time_to_takeoff if self.time_to_takeoff is not None else ""
            ),
            "takeoff": int(takeoff),
            "extinction": int(extinction),
            "max_cascade_depth": max(
                (c.cascade_depth for c in new_adopters), default=0
            ),
            "largest_referral_cascade": self._largest_referral_cascade(),
            "cascade_reach": sum(
                c.acquisition_source == "referral" for c in new_adopters
            ),
            "ticks_run": self.tick,
            "final_mean_uncertainty_nonadopters": self._mean_uncertainty_nonadopters(),
            "cost_by_stage": json.dumps(self.cost_by_stage, sort_keys=True),
        }
        summary.update(self.graph.diagnostics())
        return summary
