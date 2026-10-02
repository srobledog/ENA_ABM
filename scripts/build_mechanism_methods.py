"""Generate explicit subclass methods from the untouched, pinned v0.5 source.

This development helper is not used during simulations. The output is ordinary
reviewable Python; guards stop generation if the frozen source changes.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'src/ena_abm/model.py'
OUT = ROOT / 'src/ena_abm/mechanisms.py'
source = BASE.read_text()
node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'EntrepreneurialNetworkActivationModel')
methods = {n.name: '\n'.join(source.splitlines()[n.lineno-1:n.end_lineno]) for n in node.body if isinstance(n, ast.FunctionDef)}
def replace_once(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)

process = replace_once(methods['_process_attempt'],
    '        target_id = self.strategy_rng.choice(candidates)',
    '        target_id = self.strategy_rng.choice(candidates)\n'
    '        self._local_candidates[(self.tick, attempt_id)] = target_id')
process = replace_once(process,
    '        if not self._charge_followup(attempt, attempt_id, target_id):',
    '        if self.destination_mode == "A":\n'
    '            global_candidates = [c.consumer_id for c in self.consumers\n'
    '                                 if not c.adopted and c.consumer_id not in selected_exposure_targets]\n'
    '            if not global_candidates:\n'
    '                raise AssertionError("successful local gate must imply a global candidate")\n'
    '            target_id = self.destination_rng.choice(global_candidates)\n'
    '        if not self._charge_followup(attempt, attempt_id, target_id):')
step = replace_once(methods['step'],
    '        neighbor_counts = self._neighbor_adoption_counts(adopted_snapshot)',
    '        neighbor_counts = self._neighbor_adoption_counts(adopted_snapshot)\n'
    '        self._tick_neighbor_counts = neighbor_counts\n'
    '        self._evaluation_context = {}')
step = replace_once(step,
    '            if consumer.state == ConsumerState.UNAWARE:\n                consumer.state = ConsumerState.AWARE',
    '            self._exposure_context[event.target_id] = {\n'
    '                "target_state_before": consumer.state.value,\n'
    '                "target_previous_exposures": self._exposure_counts[event.target_id],\n'
    '                "target_degree": self.graph.degree(event.target_id),\n'
    '                "target_neighbor_adopted_share": (neighbor_counts[event.target_id] / self.graph.degree(event.target_id)\n'
    '                    if self.graph.degree(event.target_id) else 0.0),\n'
    '            }\n'
    '            if consumer.state == ConsumerState.UNAWARE:\n                consumer.state = ConsumerState.AWARE')
step = replace_once(step,
    '            if exposed or social_change:\n                consumer.state = ConsumerState.EVALUATING',
    '            active_social_change = social_change and self.reevaluation_mode == "N"\n'
    '            if exposed or active_social_change:\n'
    '                self._evaluation_context[consumer.consumer_id] = {\n'
    '                    "evaluation_cause": ("both" if exposed and active_social_change\n'
    '                        else "exposure" if exposed else "neighbor_change"),\n'
    '                    "observed_neighbor_change": bool(social_change),\n'
    '                    "first_evaluation": consumer.last_evaluation_time is None,\n'
    '                }\n'
    '                consumer.state = ConsumerState.EVALUATING')

prefix='''"""Mechanism controls v0.1 over the unmodified v0.5.0 model.

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

'''
OUT.write_text(prefix + process + '\n\n' + step + '\n')
print(OUT)
