from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .config import ModelConfig
from .model import EntrepreneurialNetworkActivationModel
from .rng import stable_seed


PARAMETER_RANGES: dict[str, tuple[float, float]] = {
    "market_sociality": (0.0, 1.0),
    "fit_mean": (0.35, 0.80),
    "status_mean": (0.20, 0.80),
    "uncertainty_mean": (0.20, 0.85),
    "delta_information": (0.0, 0.60),
    "direct_source_credibility": (0.10, 0.95),
    "referral_source_credibility": (0.10, 0.95),
    "beta_0": (-1.50, 0.50),
    "beta_individual": (1.0, 6.0),
    "beta_social": (0.0, 6.0),
    "action_budget": (8.0, 60.0),
    "seed_adopters": (1.0, 8.0),
}


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mean_to_beta(mean: float, concentration: float = 10.0) -> tuple[float, float]:
    bounded = min(0.99, max(0.01, mean))
    return bounded * concentration, (1.0 - bounded) * concentration


def _mapped_updates(parameters: dict[str, float]) -> dict[str, Any]:
    updates = dict(parameters)
    status_mean = updates.pop("status_mean", None)
    if status_mean is not None:
        updates["status_alpha"], updates["status_beta"] = _mean_to_beta(status_mean)
    uncertainty_mean = updates.pop("uncertainty_mean", None)
    if uncertainty_mean is not None:
        (
            updates["uncertainty_alpha"],
            updates["uncertainty_beta"],
        ) = _mean_to_beta(uncertainty_mean)
    if "action_budget" in updates:
        actions = int(round(updates["action_budget"]))
        updates["action_budget"] = max(0, actions)
        updates["exposure_quota"] = max(0, actions)
        updates["budget_limit"] = float(max(0, actions))
    if "seed_adopters" in updates:
        updates["seed_adopters"] = int(round(updates["seed_adopters"]))
    return updates


def _paired_run(
    base: dict[str, Any],
    *,
    parameters: dict[str, Any],
    master_seed: int,
    replicate_id: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    common = {
        **base,
        **_mapped_updates(parameters),
        "master_seed": master_seed,
        "replicate_id": replicate_id,
    }
    outputs: dict[str, dict[str, Any]] = {}
    signature: str | None = None
    for strategy in ("direct", "referral"):
        config = ModelConfig.from_dict({**common, "strategy": strategy})
        result = EntrepreneurialNetworkActivationModel(config).run()
        if signature is None:
            signature = result.initialization_signature
        elif signature != result.initialization_signature:
            raise AssertionError("paired strategies do not share initialization")
        outputs[strategy] = result.summary
    return outputs["direct"], outputs["referral"]


def _criterion_direction(mean_difference: float, threshold: float = 1.0) -> str:
    if mean_difference >= threshold:
        return "referral"
    if mean_difference <= -threshold:
        return "direct"
    return "practical_equivalence"


def run_fairness_comparison(
    specification: dict[str, Any], output_dir: Path
) -> dict[str, Any]:
    section = specification["fairness"]
    base = dict(specification["base_config"])
    seed = int(specification["experiment_seed"])
    replicates = int(section["replicates"])
    rows: list[dict[str, Any]] = []

    for criterion, network, sociality, resource_level, replicate in itertools.product(
        section["criteria"],
        section["network_types"],
        section["market_sociality"],
        section["resource_levels"],
        range(replicates),
    ):
        parameters = {
            "fairness_criterion": criterion,
            "network_type": network,
            "market_sociality": sociality,
            "action_budget": resource_level,
            "budget_limit": float(resource_level),
            "exposure_quota": resource_level,
            "direct_action_cost": 1.0,
            "referral_action_cost": 1.0,
        }
        paired_seed = stable_seed(
            seed, "fairness", network, sociality, resource_level, replicate
        )
        direct, referral = _paired_run(
            base,
            parameters=parameters,
            master_seed=paired_seed,
            replicate_id=replicate,
        )
        rows.append(
            {
                "fairness_criterion": criterion,
                "network_type": network,
                "market_sociality": sociality,
                "resource_level": resource_level,
                "replicate_id": replicate,
                "master_seed": paired_seed,
                "direct_new_adoptions": direct["new_adoptions"],
                "referral_new_adoptions": referral["new_adoptions"],
                "referral_minus_direct": (
                    referral["new_adoptions"] - direct["new_adoptions"]
                ),
                "direct_exposures": direct["exposures_delivered"],
                "referral_exposures": referral["exposures_delivered"],
                "direct_actions": direct["actions_used"],
                "referral_actions": referral["actions_used"],
                "direct_cost": direct["cost_spent"],
                "referral_cost": referral["cost_spent"],
                "direct_awareness": direct["unique_aware_nonseed"],
                "referral_awareness": referral["unique_aware_nonseed"],
                "initialization_signature": direct["initialization_signature"],
            }
        )

    grouped: dict[tuple[str, str, float, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                row["fairness_criterion"],
                row["network_type"],
                float(row["market_sociality"]),
                int(row["resource_level"]),
            )
        ].append(row)
    summaries: list[dict[str, Any]] = []
    for (criterion, network, sociality, resources), group in sorted(grouped.items()):
        differences = [float(row["referral_minus_direct"]) for row in group]
        mean_difference = statistics.fmean(differences)
        summaries.append(
            {
                "fairness_criterion": criterion,
                "network_type": network,
                "market_sociality": sociality,
                "resource_level": resources,
                "replicates": len(group),
                "mean_referral_minus_direct": mean_difference,
                "sd_referral_minus_direct": (
                    statistics.stdev(differences) if len(differences) > 1 else 0.0
                ),
                "probability_referral_beats_direct": statistics.fmean(
                    value > 0 for value in differences
                ),
                "probability_equal": statistics.fmean(
                    value == 0 for value in differences
                ),
                "direction": _criterion_direction(mean_difference),
                "mean_direct_exposures": statistics.fmean(
                    float(row["direct_exposures"]) for row in group
                ),
                "mean_referral_exposures": statistics.fmean(
                    float(row["referral_exposures"]) for row in group
                ),
            }
        )

    conditions: dict[tuple[str, float, int], list[dict[str, Any]]] = defaultdict(list)
    for row in summaries:
        conditions[
            (
                str(row["network_type"]),
                float(row["market_sociality"]),
                int(row["resource_level"]),
            )
        ].append(row)
    dependence: list[dict[str, Any]] = []
    for (network, sociality, resources), group in sorted(conditions.items()):
        directions = sorted({str(row["direction"]) for row in group})
        means = [float(row["mean_referral_minus_direct"]) for row in group]
        non_equivalent = {d for d in directions if d != "practical_equivalence"}
        sign_conflict = len(non_equivalent) > 1
        range_difference = max(means) - min(means)
        substantial = sign_conflict or range_difference >= section[
            "substantial_difference_threshold"
        ]
        dependence.append(
            {
                "network_type": network,
                "market_sociality": sociality,
                "resource_level": resources,
                "directions": "|".join(directions),
                "range_mean_difference": range_difference,
                "substantial_dependence": int(substantial),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "fairness_runs_v0.3.csv", rows)
    _write_csv(output_dir / "fairness_summary_v0.3.csv", summaries)
    _write_csv(output_dir / "fairness_dependence_check_v0.3.csv", dependence)
    stop_required = any(row["substantial_dependence"] for row in dependence)
    report = [
        "# Fairness comparison — ENA ABM v0.3",
        "",
        "This comparison uses equal normalized unit costs so that the three",
        "accounting rules can be tested without inserting an empirical cost claim.",
        "Because one completed action creates at most one exposure in the current",
        "minimal architecture, the criteria should coincide only when opportunities",
        "remain feasible and unit costs are equal.",
        "",
        f"Paired rows: {len(rows)}.",
        f"Stop condition triggered: {'YES' if stop_required else 'NO'}.",
        "",
        "A substantive stop is predefined as a direct-versus-referral direction",
        "conflict or a range of at least "
        f"{section['substantial_difference_threshold']} mean adoptions across",
        "criteria for the same network, sociality, and resource condition.",
        "",
    ]
    (output_dir / "FAIRNESS_COMPARISON_v0.3.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    return {
        "stop_required": stop_required,
        "rows": len(rows),
        "summary_rows": len(summaries),
        "files": {
            path.name: _sha256(path)
            for path in sorted(output_dir.iterdir())
            if path.is_file()
        },
    }


def _morris_trajectory(
    parameter_names: list[str],
    levels: int,
    rng: random.Random,
) -> tuple[list[list[float]], list[str], float]:
    delta = levels / (2.0 * (levels - 1.0))
    grid = [index / (levels - 1.0) for index in range(levels)]
    directions = {name: rng.choice((-1, 1)) for name in parameter_names}
    point: dict[str, float] = {}
    for name in parameter_names:
        feasible = [
            value
            for value in grid
            if 0.0 <= value + directions[name] * delta <= 1.0
        ]
        point[name] = rng.choice(feasible)
    order = list(parameter_names)
    rng.shuffle(order)
    points = [[point[name] for name in parameter_names]]
    for changed in order:
        point = dict(point)
        point[changed] += directions[changed] * delta
        points.append([point[name] for name in parameter_names])
    return points, order, delta


def _scale_point(names: list[str], values: list[float]) -> dict[str, float]:
    output: dict[str, float] = {}
    for name, normalized in zip(names, values):
        low, high = PARAMETER_RANGES[name]
        output[name] = low + normalized * (high - low)
    return output


def _response(direct: list[dict[str, Any]], referral: list[dict[str, Any]]) -> dict[str, float]:
    mean_direct = statistics.fmean(float(row["new_adoptions"]) for row in direct)
    mean_referral = statistics.fmean(float(row["new_adoptions"]) for row in referral)
    awareness = statistics.fmean(
        (
            float(d["unique_aware_nonseed"])
            + float(r["unique_aware_nonseed"])
        )
        / 2.0
        for d, r in zip(direct, referral)
    )
    takeoff_difference = statistics.fmean(
        float(r["takeoff"]) - float(d["takeoff"]) for d, r in zip(direct, referral)
    )
    return {
        "paired_adoption_difference": mean_referral - mean_direct,
        "mean_adoptions": (mean_referral + mean_direct) / 2.0,
        "mean_awareness": awareness,
        "paired_takeoff_difference": takeoff_difference,
    }


def run_morris_screening(
    specification: dict[str, Any], output_dir: Path
) -> dict[str, Any]:
    section = specification["morris"]
    base = dict(specification["base_config"])
    names = list(PARAMETER_RANGES)
    rng = random.Random(int(specification["experiment_seed"]))
    raw_runs: list[dict[str, Any]] = []
    point_rows: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []

    for trajectory in range(int(section["trajectories"])):
        points, order, delta = _morris_trajectory(
            names, int(section["levels"]), rng
        )
        previous_response: dict[str, float] | None = None
        for point_index, normalized in enumerate(points):
            parameters = _scale_point(names, normalized)
            direct_rows: list[dict[str, Any]] = []
            referral_rows: list[dict[str, Any]] = []
            for replicate in range(int(section["replicates_per_point"])):
                paired_seed = stable_seed(
                    int(specification["experiment_seed"]),
                    "morris",
                    trajectory,
                    replicate,
                )
                direct, referral = _paired_run(
                    base,
                    parameters=parameters,
                    master_seed=paired_seed,
                    replicate_id=replicate,
                )
                direct_rows.append(direct)
                referral_rows.append(referral)
                for strategy, row in (("direct", direct), ("referral", referral)):
                    raw_runs.append(
                        {
                            "trajectory": trajectory,
                            "point": point_index,
                            "replicate_id": replicate,
                            "strategy": strategy,
                            "master_seed": paired_seed,
                            **{name: parameters[name] for name in names},
                            "new_adoptions": row["new_adoptions"],
                            "unique_aware_nonseed": row["unique_aware_nonseed"],
                            "takeoff": row["takeoff"],
                            "extinction": row["extinction"],
                            "actions_used": row["actions_used"],
                        }
                    )
            current = _response(direct_rows, referral_rows)
            point_rows.append(
                {
                    "trajectory": trajectory,
                    "point": point_index,
                    "changed_from_previous": "" if point_index == 0 else order[point_index - 1],
                    **{name: parameters[name] for name in names},
                    **current,
                }
            )
            if previous_response is not None:
                changed = order[point_index - 1]
                direction = (
                    normalized[names.index(changed)]
                    - points[point_index - 1][names.index(changed)]
                )
                for outcome, value in current.items():
                    effects.append(
                        {
                            "trajectory": trajectory,
                            "parameter": changed,
                            "outcome": outcome,
                            "elementary_effect": (
                                value - previous_response[outcome]
                            )
                            / direction,
                            "normalized_step": direction,
                            "delta": delta,
                        }
                    )
            previous_response = current

    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in effects:
        grouped[(row["parameter"], row["outcome"])].append(
            float(row["elementary_effect"])
        )
    indices: list[dict[str, Any]] = []
    for (parameter, outcome), values in sorted(grouped.items()):
        indices.append(
            {
                "parameter": parameter,
                "outcome": outcome,
                "n_effects": len(values),
                "mu": statistics.fmean(values),
                "mu_star": statistics.fmean(abs(value) for value in values),
                "sigma": statistics.stdev(values) if len(values) > 1 else 0.0,
            }
        )

    degenerate: list[dict[str, Any]] = []
    n_nonseed = int(base["n_consumers"]) - 1
    for row in point_rows:
        mean_adoptions = float(row["mean_adoptions"])
        if mean_adoptions <= 0.5 or mean_adoptions >= n_nonseed - 0.5:
            degenerate.append(
                {
                    "trajectory": row["trajectory"],
                    "point": row["point"],
                    "degenerate_type": (
                        "near_zero_adoption"
                        if mean_adoptions <= 0.5
                        else "near_universal_adoption"
                    ),
                    **{name: row[name] for name in names},
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "morris_runs_v0.3.csv", raw_runs)
    _write_csv(output_dir / "morris_points_v0.3.csv", point_rows)
    _write_csv(output_dir / "morris_elementary_effects_v0.3.csv", effects)
    _write_csv(output_dir / "morris_indices_v0.3.csv", indices)
    if degenerate:
        _write_csv(output_dir / "morris_degenerate_regions_v0.3.csv", degenerate)
    else:
        (output_dir / "morris_degenerate_regions_v0.3.csv").write_text(
            "trajectory,point,degenerate_type\n", encoding="utf-8"
        )
    return {
        "trajectories": int(section["trajectories"]),
        "runs": len(raw_runs),
        "effects": len(effects),
        "degenerate_points": len(degenerate),
        "files": {
            path.name: _sha256(path)
            for path in sorted(output_dir.iterdir())
            if path.is_file()
        },
    }


def _diagnostic_scenarios(base: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = [
        {"scenario": "baseline", "updates": {}},
        {"scenario": "network_ring", "updates": {"network_type": "ring"}},
        {
            "scenario": "network_preferential",
            "updates": {"network_type": "preferential_attachment"},
        },
        {"scenario": "sociality_zero", "updates": {"market_sociality": 0.0}},
        {"scenario": "sociality_high", "updates": {"market_sociality": 0.9}},
        {"scenario": "uncertainty_low", "updates": {"uncertainty_mean": 0.25}},
        {"scenario": "uncertainty_high", "updates": {"uncertainty_mean": 0.80}},
        {"scenario": "status_low", "updates": {"status_mean": 0.25}},
        {"scenario": "status_high", "updates": {"status_mean": 0.75}},
        {
            "scenario": "credibility_equal",
            "updates": {
                "direct_source_credibility": 0.60,
                "referral_source_credibility": 0.60,
            },
        },
        {
            "scenario": "referral_credibility_low",
            "updates": {
                "direct_source_credibility": 0.60,
                "referral_source_credibility": 0.20,
            },
        },
        {
            "scenario": "referral_credibility_high",
            "updates": {
                "direct_source_credibility": 0.60,
                "referral_source_credibility": 0.90,
            },
        },
        {"scenario": "opportunities_low", "updates": {"seed_adopters": 1}},
        {"scenario": "opportunities_high", "updates": {"seed_adopters": 7}},
        {"scenario": "resources_scarce", "updates": {"action_budget": 10}},
        {"scenario": "resources_abundant", "updates": {"action_budget": 60}},
        {
            "scenario": "fairness_equal_budget",
            "updates": {"fairness_criterion": "equal_budget"},
        },
        {
            "scenario": "fairness_equal_exposures",
            "updates": {"fairness_criterion": "equal_exposures"},
        },
        {
            "scenario": "budget_referral_cost_low",
            "updates": {
                "fairness_criterion": "equal_budget",
                "direct_action_cost": 1.0,
                "referral_action_cost": 0.5,
            },
        },
        {
            "scenario": "budget_referral_cost_high",
            "updates": {
                "fairness_criterion": "equal_budget",
                "direct_action_cost": 1.0,
                "referral_action_cost": 2.0,
            },
        },
    ]
    return scenarios


def run_diagnostics(
    specification: dict[str, Any], output_dir: Path
) -> dict[str, Any]:
    section = specification["diagnostics"]
    base = dict(specification["base_config"])
    rows: list[dict[str, Any]] = []
    scenarios = _diagnostic_scenarios(base)
    for scenario in scenarios:
        for replicate in range(int(section["replicates"])):
            paired_seed = stable_seed(
                int(specification["experiment_seed"]),
                "diagnostic",
                replicate,
            )
            direct, referral = _paired_run(
                base,
                parameters=scenario["updates"],
                master_seed=paired_seed,
                replicate_id=replicate,
            )
            for strategy, result in (("direct", direct), ("referral", referral)):
                rows.append(
                    {
                        "scenario": scenario["scenario"],
                        "strategy": strategy,
                        "replicate_id": replicate,
                        "master_seed": paired_seed,
                        "new_adoptions": result["new_adoptions"],
                        "unique_aware_nonseed": result["unique_aware_nonseed"],
                        "mean_time_to_adoption": result["mean_time_to_adoption"],
                        "takeoff": result["takeoff"],
                        "extinction": result["extinction"],
                        "cascade_reach": result["cascade_reach"],
                        "max_cascade_depth": result["max_cascade_depth"],
                        "cost_per_new_adopter": result["cost_per_new_adopter"],
                        "adoptions_per_action": result["adoptions_per_action"],
                        "adoptions_per_budget_unit": result[
                            "adoptions_per_budget_unit"
                        ],
                        "actions_used": result["actions_used"],
                        "cost_spent": result["cost_spent"],
                        "exposures_delivered": result["exposures_delivered"],
                        "initialization_signature": result[
                            "initialization_signature"
                        ],
                    }
                )

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["scenario"], row["strategy"])].append(row)
    summaries: list[dict[str, Any]] = []
    for (scenario, strategy), group in sorted(grouped.items()):
        adoptions = [float(row["new_adoptions"]) for row in group]
        summaries.append(
            {
                "scenario": scenario,
                "strategy": strategy,
                "replicates": len(group),
                "mean_new_adoptions": statistics.fmean(adoptions),
                "sd_new_adoptions": statistics.stdev(adoptions),
                "mean_awareness": statistics.fmean(
                    float(row["unique_aware_nonseed"]) for row in group
                ),
                "takeoff_probability": statistics.fmean(
                    float(row["takeoff"]) for row in group
                ),
                "extinction_probability": statistics.fmean(
                    float(row["extinction"]) for row in group
                ),
                "mean_actions_used": statistics.fmean(
                    float(row["actions_used"]) for row in group
                ),
                "mean_exposures": statistics.fmean(
                    float(row["exposures_delivered"]) for row in group
                ),
            }
        )

    pairs: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        pairs[(row["scenario"], int(row["replicate_id"]))][row["strategy"]] = row
    paired_rows: list[dict[str, Any]] = []
    for (scenario, replicate), strategies in sorted(pairs.items()):
        direct = strategies["direct"]
        referral = strategies["referral"]
        absolute = float(referral["new_adoptions"]) - float(direct["new_adoptions"])
        denominator = max(1.0, float(direct["new_adoptions"]))
        paired_rows.append(
            {
                "scenario": scenario,
                "replicate_id": replicate,
                "absolute_difference": absolute,
                "relative_difference": absolute / denominator,
                "referral_beats_direct": int(absolute > 0),
            }
        )
    paired_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in paired_rows:
        paired_groups[row["scenario"]].append(row)
    paired_summary: list[dict[str, Any]] = []
    for scenario, group in sorted(paired_groups.items()):
        absolute = [float(row["absolute_difference"]) for row in group]
        relative = [float(row["relative_difference"]) for row in group]
        paired_summary.append(
            {
                "scenario": scenario,
                "replicates": len(group),
                "mean_absolute_difference": statistics.fmean(absolute),
                "sd_absolute_difference": statistics.stdev(absolute),
                "mean_relative_difference": statistics.fmean(relative),
                "probability_referral_beats_direct": statistics.fmean(
                    float(row["referral_beats_direct"]) for row in group
                ),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "diagnostic_runs_v0.3.csv", rows)
    _write_csv(output_dir / "diagnostic_summary_v0.3.csv", summaries)
    _write_csv(output_dir / "diagnostic_paired_runs_v0.3.csv", paired_rows)
    _write_csv(output_dir / "diagnostic_paired_summary_v0.3.csv", paired_summary)
    return {
        "scenarios": len(scenarios),
        "runs": len(rows),
        "files": {
            path.name: _sha256(path)
            for path in sorted(output_dir.iterdir())
            if path.is_file()
        },
    }


def run_validation(config_path: Path, output_root: Path) -> dict[str, Any]:
    specification = json.loads(config_path.read_text(encoding="utf-8"))
    output_root.mkdir(parents=True, exist_ok=True)
    fairness = run_fairness_comparison(specification, output_root / "fairness")
    manifest: dict[str, Any] = {
        "model_version": "0.3.0",
        "specification_version": "0.3",
        "experiment_seed": specification["experiment_seed"],
        "fairness": fairness,
        "stopped_after_fairness": bool(fairness["stop_required"]),
        "interpretation_status": "model_diagnostics_only_not_article_evidence",
    }
    if not fairness["stop_required"]:
        manifest["morris"] = run_morris_screening(
            specification, output_root / "morris"
        )
        manifest["diagnostics"] = run_diagnostics(
            specification, output_root / "diagnostics"
        )
    manifest_path = output_root / "validation_manifest_v0.3.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
