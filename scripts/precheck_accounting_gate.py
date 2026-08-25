"""Predeclared v0.4 stop-gate diagnostic for the two cost conventions."""

from __future__ import annotations

import statistics

from ena_abm.config import ModelConfig
from ena_abm.model import EntrepreneurialNetworkActivationModel
from ena_abm.rng import stable_seed


BASE = {
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
    "actions_per_tick": 2,
    "horizon": 30,
    "direct_exposure_probability": 0.512,
    "referral_acceptance_probability": 0.8,
    "referral_neighbor_availability_probability": 0.8,
    "referral_introduction_probability": 0.8,
    "direct_source_credibility": 0.60,
    "referral_source_credibility": 0.60,
    "master_seed": 2026072404,
}


def main() -> None:
    grid = [0.25 * index for index in range(1, 13)]
    replicates = 50
    for accounting in ("upfront_expected", "staged"):
        curve = []
        for relative_cost in grid:
            differences = []
            for replicate in range(replicates):
                seed = stable_seed(
                    2026072404, "accounting_gate", accounting, replicate
                )
                common = {
                    **BASE,
                    "cost_accounting": accounting,
                    "master_seed": seed,
                    "replicate_id": replicate,
                }
                direct = EntrepreneurialNetworkActivationModel(
                    ModelConfig.from_dict({**common, "strategy": "direct"})
                ).run()
                referral = EntrepreneurialNetworkActivationModel(
                    ModelConfig.from_dict(
                        {
                            **common,
                            "strategy": "referral",
                            "referral_action_cost": relative_cost,
                        }
                    )
                ).run()
                if direct.initialization_signature != referral.initialization_signature:
                    raise AssertionError("paired initialization failed")
                differences.append(
                    referral.summary["new_adoptions"]
                    - direct.summary["new_adoptions"]
                )
            curve.append((relative_cost, statistics.fmean(differences)))
        competitive = [r for r, difference in curve if difference >= 0]
        r_star = max(competitive) if competitive else None
        print(accounting, "r_star_grid", r_star)
        print("curve", curve)


if __name__ == "__main__":
    main()
