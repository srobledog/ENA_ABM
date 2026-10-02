"""Mechanism controls v0.1 over the unmodified v0.5.0 model.

_process_attempt and step are explicit copies of the two frozen methods with
guarded interventions. See scripts/build_mechanism_methods.py for the exact
transformations. All remaining behavior is inherited from the frozen model.
"""
from __future__ import annotations
import math
import random
from .agents import ConsumerState
from .events import ActivationAttempt, ExposureEvent, PendingAdoption
from .model import EntrepreneurialNetworkActivationModel
from .rng import stable_seed


class MechanismModel(EntrepreneurialNetworkActivationModel):
    def __init__(self, config, *, destination_mode="L", beta_social_mode=1,
                 reevaluation_mode="N", **kwargs):
        if destination_mode not in {"L", "A"} or beta_social_mode not in {0, 1} or reevaluation_mode not in {"N", "E"}:
            raise ValueError("invalid mechanism intervention")
        self.destination_mode = destination_mode
        self.beta_social_mode = beta_social_mode
        self.reevaluation_mode = reevaluation_mode
        effective = config if beta_social_mode else config.with_updates(beta_social=0.0)
        super().__init__(effective, **kwargs)
        self.destination_rng = random.Random(stable_seed(config.master_seed, "mechanisms_destination"))
        self._local_candidates = {}
        self._exposure_counts = [0] * config.n_consumers
        self._exposure_context = {}
        self._evaluation_context = {}
        self._tick_neighbor_counts = []

    def _record_attempt(self, attempt, **kwargs):
        super()._record_attempt(attempt, **kwargs)
        self.event_records[-1]["local_candidate_id"] = self._local_candidates.get((self.tick, kwargs["attempt_id"]), "")

    def _record_exposure(self, event, **kwargs):
        super()._record_exposure(event, **kwargs)
        self.event_records[-1].update(self._exposure_context[event.target_id])
        self.event_records[-1]["local_candidate_id"] = self._local_candidates.get((self.tick, event.attempt_id), "")
        self._exposure_counts[event.target_id] += 1

    def _record_evaluation(self, pending, adopted):
        super()._record_evaluation(pending, adopted)
        row = self.event_records[-1]
        row.update(self._evaluation_context[pending.consumer_id])
        row["individual_utility_component"] = self.config.beta_individual * (1.0 - pending.social_reliance) * pending.individual_evaluation
        row["social_utility_component"] = self.config.beta_social * pending.social_reliance * (2.0 * pending.social_evidence - 1.0)

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
        self._local_candidates[(self.tick, attempt_id)] = target_id
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
        if self.destination_mode == "A":
            global_candidates = [c.consumer_id for c in self.consumers
                                 if not c.adopted and c.consumer_id not in selected_exposure_targets]
            if not global_candidates:
                raise AssertionError("successful local gate must imply a global candidate")
            target_id = self.destination_rng.choice(global_candidates)
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

    def step(self) -> None:
        self.tick += 1
        adopted_snapshot = self._adopted_snapshot()
        neighbor_counts = self._neighbor_adoption_counts(adopted_snapshot)
        self._tick_neighbor_counts = neighbor_counts
        self._evaluation_context = {}
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
            self._exposure_context[event.target_id] = {
                "target_state_before": consumer.state.value,
                "target_previous_exposures": self._exposure_counts[event.target_id],
                "target_degree": self.graph.degree(event.target_id),
                "target_neighbor_adopted_share": (neighbor_counts[event.target_id] / self.graph.degree(event.target_id)
                    if self.graph.degree(event.target_id) else 0.0),
            }
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
            active_social_change = social_change and self.reevaluation_mode == "N"
            if exposed or active_social_change:
                self._evaluation_context[consumer.consumer_id] = {
                    "evaluation_cause": ("both" if exposed and active_social_change
                        else "exposure" if exposed else "neighbor_change"),
                    "observed_neighbor_change": bool(social_change),
                    "first_evaluation": consumer.last_evaluation_time is None,
                }
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
