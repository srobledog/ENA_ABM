from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from .config import ModelConfig
from .model import EntrepreneurialNetworkActivationModel
from .rng import stable_seed


Z_975 = 1.959963984540054


@dataclass(frozen=True)
class DiagnosticScenario:
    name: str
    factor: str
    level: str
    description: str
    updates: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "factor": self.factor,
            "level": self.level,
            "description": self.description,
            "updates": self.updates,
        }


def mean_to_beta(mean: float, concentration: float = 10.0) -> tuple[float, float]:
    if not 0.0 < mean < 1.0:
        raise ValueError("beta-distribution mean must be in (0, 1)")
    return mean * concentration, (1.0 - mean) * concentration


def mapped_updates(updates: dict[str, Any]) -> dict[str, Any]:
    mapped = dict(updates)
    status_mean = mapped.pop("status_mean", None)
    if status_mean is not None:
        mapped["status_alpha"], mapped["status_beta"] = mean_to_beta(
            float(status_mean)
        )
    uncertainty_mean = mapped.pop("uncertainty_mean", None)
    if uncertainty_mean is not None:
        mapped["uncertainty_alpha"], mapped["uncertainty_beta"] = mean_to_beta(
            float(uncertainty_mean)
        )
    return mapped


def paired_grid_worker(
    payload: tuple[
        dict[str, Any],
        dict[str, Any],
        str,
        int,
        list[float],
        int,
    ]
) -> list[dict[str, Any]]:
    base, scenario_dict, accounting, replicate, r_grid, experiment_seed = payload
    scenario = DiagnosticScenario(**scenario_dict)
    paired_seed = stable_seed(
        experiment_seed, "break_even_v0.4", scenario.name, replicate
    )
    common = {
        **base,
        **mapped_updates(scenario.updates),
        "cost_accounting": accounting,
        "master_seed": paired_seed,
        "replicate_id": replicate,
    }
    direct = EntrepreneurialNetworkActivationModel(
        ModelConfig.from_dict({**common, "strategy": "direct"})
    ).run()
    rows: list[dict[str, Any]] = []
    for relative_cost in r_grid:
        referral = EntrepreneurialNetworkActivationModel(
            ModelConfig.from_dict(
                {
                    **common,
                    "strategy": "referral",
                    "referral_action_cost": float(relative_cost),
                }
            )
        ).run()
        if direct.initialization_signature != referral.initialization_signature:
            raise AssertionError("paired initialization failed")
        direct_summary = direct.summary
        referral_summary = referral.summary
        budget = float(direct_summary["budget_limit"])
        rows.append(
            {
                "scenario": scenario.name,
                "factor": scenario.factor,
                "level": scenario.level,
                "accounting": accounting,
                "r": float(relative_cost),
                "replicate": replicate,
                "master_seed": paired_seed,
                "initialization_signature": direct.initialization_signature,
                "direct_adoptions": direct_summary["new_adoptions"],
                "referral_adoptions": referral_summary["new_adoptions"],
                "delta_adoptions": (
                    referral_summary["new_adoptions"]
                    - direct_summary["new_adoptions"]
                ),
                "direct_allocated_efficiency": (
                    direct_summary["new_adoptions"] / budget if budget else 0.0
                ),
                "referral_allocated_efficiency": (
                    referral_summary["new_adoptions"] / budget if budget else 0.0
                ),
                "delta_allocated_efficiency": (
                    (
                        referral_summary["new_adoptions"]
                        - direct_summary["new_adoptions"]
                    )
                    / budget
                    if budget
                    else 0.0
                ),
                "direct_spent_efficiency": direct_summary[
                    "adoptions_per_budget_unit"
                ],
                "referral_spent_efficiency": referral_summary[
                    "adoptions_per_budget_unit"
                ],
                "direct_attempts": direct_summary["attempts_started"],
                "referral_attempts": referral_summary["attempts_started"],
                "direct_exposures": direct_summary["exposures_delivered"],
                "referral_exposures": referral_summary["exposures_delivered"],
                "direct_adoptions_per_exposure": direct_summary[
                    "adoptions_per_exposure"
                ],
                "referral_adoptions_per_exposure": referral_summary[
                    "adoptions_per_exposure"
                ],
                "direct_cost_spent": direct_summary["cost_spent"],
                "referral_cost_spent": referral_summary["cost_spent"],
                "direct_unused_budget": direct_summary["unused_budget"],
                "referral_unused_budget": referral_summary["unused_budget"],
                "direct_takeoff": direct_summary["takeoff"],
                "referral_takeoff": referral_summary["takeoff"],
                "direct_extinction": direct_summary["extinction"],
                "referral_extinction": referral_summary["extinction"],
                "direct_max_cascade_depth": direct_summary["max_cascade_depth"],
                "referral_max_cascade_depth": referral_summary[
                    "max_cascade_depth"
                ],
                "referral_unavailable_opportunities": referral_summary[
                    "unavailable_opportunities"
                ],
                "referral_requests_accepted": referral_summary[
                    "requests_accepted"
                ],
                "referral_failed_attempts": referral_summary["failed_attempts"],
                "referral_eligible_sources_seen": referral_summary[
                    "eligible_sources_seen"
                ],
            }
        )
    return rows


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize_grid(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (str(row["scenario"]), str(row["accounting"]), float(row["r"]))
        ].append(row)
    summaries: list[dict[str, Any]] = []
    for (scenario, accounting, relative_cost), group in sorted(groups.items()):
        differences = [float(row["delta_adoptions"]) for row in group]
        mean_difference = statistics.fmean(differences)
        sd_difference = (
            statistics.stdev(differences) if len(differences) > 1 else 0.0
        )
        mcse = sd_difference / math.sqrt(len(differences))
        half_width = Z_975 * mcse
        efficiency = [
            float(row["delta_allocated_efficiency"]) for row in group
        ]
        summaries.append(
            {
                "scenario": scenario,
                "factor": group[0]["factor"],
                "level": group[0]["level"],
                "accounting": accounting,
                "r": relative_cost,
                "replicates": len(group),
                "mean_delta": mean_difference,
                "sd_delta": sd_difference,
                "mcse_delta": mcse,
                "ci95_lower": mean_difference - half_width,
                "ci95_upper": mean_difference + half_width,
                "median_delta": statistics.median(differences),
                "p10_delta": _quantile(differences, 0.10),
                "p90_delta": _quantile(differences, 0.90),
                "probability_referral_higher": statistics.fmean(
                    value > 0 for value in differences
                ),
                "probability_equal": statistics.fmean(
                    value == 0 for value in differences
                ),
                "probability_referral_not_lower": statistics.fmean(
                    value >= 0 for value in differences
                ),
                "mean_delta_allocated_efficiency": statistics.fmean(efficiency),
                "mean_direct_adoptions": statistics.fmean(
                    float(row["direct_adoptions"]) for row in group
                ),
                "mean_referral_adoptions": statistics.fmean(
                    float(row["referral_adoptions"]) for row in group
                ),
                "mean_direct_attempts": statistics.fmean(
                    float(row["direct_attempts"]) for row in group
                ),
                "mean_referral_attempts": statistics.fmean(
                    float(row["referral_attempts"]) for row in group
                ),
                "mean_direct_exposures": statistics.fmean(
                    float(row["direct_exposures"]) for row in group
                ),
                "mean_referral_exposures": statistics.fmean(
                    float(row["referral_exposures"]) for row in group
                ),
                "mean_direct_unused_budget": statistics.fmean(
                    float(row["direct_unused_budget"]) for row in group
                ),
                "mean_referral_unused_budget": statistics.fmean(
                    float(row["referral_unused_budget"]) for row in group
                ),
                "mean_referral_unavailable_opportunities": statistics.fmean(
                    float(row["referral_unavailable_opportunities"])
                    for row in group
                ),
            }
        )
    return summaries


def _supremum(rows: list[dict[str, Any]], field: str, threshold: float) -> float | None:
    competitive = [float(row["r"]) for row in rows if float(row[field]) >= threshold]
    return max(competitive) if competitive else None


def _crossing_count(rows: list[dict[str, Any]], field: str = "mean_delta") -> int:
    signs: list[int] = []
    for row in rows:
        value = float(row[field])
        signs.append(1 if value > 0 else -1 if value < 0 else 0)
    collapsed = [sign for sign in signs if sign != 0]
    return sum(a != b for a, b in zip(collapsed, collapsed[1:]))


def _competitive_regions(rows: list[dict[str, Any]]) -> str:
    regions: list[tuple[float, float]] = []
    start: float | None = None
    previous: float | None = None
    for row in rows:
        relative_cost = float(row["r"])
        if float(row["mean_delta"]) >= 0:
            if start is None:
                start = relative_cost
            previous = relative_cost
        elif start is not None:
            regions.append((start, previous if previous is not None else start))
            start = None
            previous = None
    if start is not None:
        regions.append((start, previous if previous is not None else start))
    return "|".join(f"[{low:.2f},{high:.2f}]" for low, high in regions)


def threshold_summary(summaries: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in summaries:
        groups[(str(row["scenario"]), str(row["accounting"]))].append(row)
    output: list[dict[str, Any]] = []
    for (scenario, accounting), group in sorted(groups.items()):
        ordered = sorted(group, key=lambda row: float(row["r"]))
        upward_jumps = [
            float(right["mean_delta"]) - float(left["mean_delta"])
            for left, right in zip(ordered, ordered[1:])
        ]
        material_upward = sum(
            jump
            > Z_975
            * math.sqrt(
                float(left["mcse_delta"]) ** 2
                + float(right["mcse_delta"]) ** 2
            )
            for jump, left, right in zip(
                upward_jumps, ordered, ordered[1:]
            )
        )
        r_primary = _supremum(ordered, "mean_delta", 0.0)
        r_conservative = _supremum(ordered, "ci95_lower", 0.0)
        r_probability = _supremum(
            ordered, "probability_referral_higher", 0.50
        )
        r_efficiency = _supremum(
            ordered, "mean_delta_allocated_efficiency", 0.0
        )
        at_upper = r_primary == max(float(row["r"]) for row in ordered)
        no_competitive = r_primary is None
        crossings = _crossing_count(ordered)
        interpretable = (
            not at_upper
            and not no_competitive
            and crossings <= 1
            and material_upward == 0
        )
        output.append(
            {
                "scenario": scenario,
                "factor": ordered[0]["factor"],
                "level": ordered[0]["level"],
                "accounting": accounting,
                "r_star_primary_grid": r_primary if r_primary is not None else "",
                "r_star_conservative_grid": (
                    r_conservative if r_conservative is not None else ""
                ),
                "r_star_probability_grid": (
                    r_probability if r_probability is not None else ""
                ),
                "r_star_efficiency_grid": (
                    r_efficiency if r_efficiency is not None else ""
                ),
                "crossing_count": crossings,
                "material_upward_jumps": material_upward,
                "competitive_regions": _competitive_regions(ordered),
                "no_competitive_region": int(no_competitive),
                "competitive_through_upper_bound": int(at_upper),
                "interpretable_single_threshold": int(interpretable),
                "grid_min": min(float(row["r"]) for row in ordered),
                "grid_max": max(float(row["r"]) for row in ordered),
                "grid_points": len(ordered),
            }
        )
    return output


def refinement_grid(
    summaries: Iterable[dict[str, Any]],
    *,
    tolerance: float = 0.05,
    lower_bound: float = 0.25,
    upper_bound: float = 3.0,
) -> dict[tuple[str, str], list[float]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in summaries:
        groups[(str(row["scenario"]), str(row["accounting"]))].append(row)
    output: dict[tuple[str, str], list[float]] = {}
    for key, group in groups.items():
        ordered = sorted(group, key=lambda row: float(row["r"]))
        candidates: set[float] = set()
        for left, right in zip(ordered, ordered[1:]):
            left_value = float(left["mean_delta"])
            right_value = float(right["mean_delta"])
            if (
                left_value == 0.0
                or right_value == 0.0
                or (left_value > 0) != (right_value > 0)
            ):
                current = float(left["r"])
                right_r = float(right["r"])
                while current <= right_r + 1e-9:
                    candidates.add(round(current, 10))
                    current += tolerance
        existing = {round(float(row["r"]), 10) for row in ordered}
        refined = sorted(
            value
            for value in candidates - existing
            if lower_bound <= value <= upper_bound
        )
        output[key] = refined
    return output


def scenario_manifest(scenarios: Iterable[DiagnosticScenario]) -> str:
    return json.dumps([scenario.to_dict() for scenario in scenarios], indent=2)
