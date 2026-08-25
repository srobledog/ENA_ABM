"""Export deterministic diagnostic traces for the v0.4 activation process."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ena_abm.config import ModelConfig
from ena_abm.model import EntrepreneurialNetworkActivationModel
from ena_abm.rng import stable_seed


BASE: dict[str, Any] = {
    "n_consumers": 100,
    "network_type": "small_world",
    "mean_degree": 6,
    "rewire_probability": 0.10,
    "market_sociality": 0.50,
    "seed_adopters": 3,
    "fairness_criterion": "equal_budget",
    "action_budget": 999,
    "budget_limit": 40.0,
    "exposure_quota": 999,
    "direct_action_cost": 1.0,
    "referral_action_cost": 1.0,
    "cost_accounting": "upfront_expected",
    "actions_per_tick": 2,
    "horizon": 30,
    "direct_exposure_probability": 0.512,
    "referral_acceptance_probability": 0.80,
    "referral_neighbor_availability_probability": 0.80,
    "referral_introduction_probability": 0.80,
    "direct_source_credibility": 0.60,
    "referral_source_credibility": 0.60,
}


CASES: list[tuple[str, dict[str, Any]]] = [
    ("baseline_direct", {"strategy": "direct"}),
    ("baseline_referral", {"strategy": "referral"}),
    (
        "failed_direct_contact",
        {
            "strategy": "direct",
            "n_consumers": 20,
            "mean_degree": 4,
            "seed_adopters": 1,
            "horizon": 1,
            "actions_per_tick": 1,
            "budget_limit": 1.0,
            "direct_exposure_probability": 0.0,
        },
    ),
    (
        "rejected_referral_request",
        {
            "strategy": "referral",
            "n_consumers": 20,
            "mean_degree": 4,
            "seed_adopters": 1,
            "horizon": 1,
            "actions_per_tick": 1,
            "budget_limit": 1.0,
            "referral_acceptance_probability": 0.0,
        },
    ),
    (
        "no_eligible_neighbor",
        {
            "strategy": "referral",
            "n_consumers": 20,
            "mean_degree": 4,
            "seed_adopters": 1,
            "horizon": 1,
            "actions_per_tick": 1,
            "budget_limit": 1.0,
            "referral_neighbor_availability_probability": 0.0,
        },
    ),
    (
        "no_referrer_available",
        {
            "strategy": "referral",
            "n_consumers": 20,
            "mean_degree": 4,
            "seed_adopters": 0,
            "horizon": 1,
            "actions_per_tick": 1,
            "budget_limit": 1.0,
        },
    ),
]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot write empty process registry")
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    output = Path("outputs/process_registry_v0_4")
    events: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for case, updates in CASES:
        seed_key = "baseline_pair" if case.startswith("baseline_") else case
        seed = stable_seed(2026072404, "process_registry", seed_key)
        config = ModelConfig.from_dict(
            {**BASE, **updates, "master_seed": seed, "replicate_id": 0}
        )
        result = EntrepreneurialNetworkActivationModel(config).run()
        events.extend(
            {
                "diagnostic_case": case,
                "strategy": config.strategy,
                "cost_accounting": config.cost_accounting,
                **row,
            }
            for row in result.events
        )
        summaries.append(
            {
                "diagnostic_case": case,
                "master_seed": seed,
                "initialization_signature": result.initialization_signature,
                "strategy": config.strategy,
                "attempts_started": result.summary["attempts_started"],
                "failed_attempts": result.summary["failed_attempts"],
                "requests_accepted": result.summary["requests_accepted"],
                "exposures_delivered": result.summary["exposures_delivered"],
                "evaluation_events": result.summary["evaluation_events"],
                "new_adoptions": result.summary["new_adoptions"],
                "unavailable_opportunities": result.summary[
                    "unavailable_opportunities"
                ],
                "cost_spent": result.summary["cost_spent"],
                "unused_budget": result.summary["unused_budget"],
            }
        )
    write_csv(output / "process_event_registry_v0.4.csv", events)
    write_csv(output / "process_case_summary_v0.4.csv", summaries)
    (output / "process_registry_manifest_v0.4.json").write_text(
        json.dumps(
            {
                "status": "deterministic_diagnostic_traces_not_empirical_data",
                "cases": [case for case, _ in CASES],
                "event_rows": len(events),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
