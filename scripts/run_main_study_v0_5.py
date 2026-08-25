"""Execute ENA ABM v0.5 as a theoretical main simulation study.

The behavioral model is the frozen v0.4 implementation. All values are
diagnostic theoretical parameters and must not be described as empirically
calibrated estimates.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import random
import statistics
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from ena_abm.break_even import refinement_grid, threshold_summary
from ena_abm.config import ModelConfig
from ena_abm.model import EntrepreneurialNetworkActivationModel
from ena_abm.rng import stable_seed


Z_975 = 1.959963984540054

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
    "fit_mean": 0.60,
    "fit_sd": 0.15,
    "status_alpha": 4.0,
    "status_beta": 3.0,
    "uncertainty_alpha": 3.0,
    "uncertainty_beta": 2.0,
    "minimum_uncertainty": 0.05,
    "delta_information": 0.25,
    "direct_exposure_probability": 0.512,
    "referral_acceptance_probability": 0.80,
    "referral_neighbor_availability_probability": 0.80,
    "referral_introduction_probability": 0.80,
    "direct_source_credibility": 0.60,
    "referral_source_credibility": 0.60,
    "beta_0": -0.50,
    "beta_individual": 4.00,
    "beta_social": 3.00,
    "takeoff_share": 0.10,
    "quiet_period": 5,
    "allow_repeated_direct_contact": True,
}

PROCESS_FIELDS = [
    "new_adoptions",
    "attempts_started",
    "failed_attempts",
    "exposures_delivered",
    "evaluation_events",
    "cost_spent",
    "unused_budget",
    "cost_per_effective_exposure",
    "cost_per_new_adopter",
    "exposures_per_attempt",
    "adoptions_per_exposure",
    "adoptions_per_budget_unit",
    "takeoff",
    "extinction",
    "max_cascade_depth",
    "largest_referral_cascade",
    "cascade_reach",
    "time_to_first_new_adoption",
    "mean_time_to_adoption",
    "time_to_takeoff",
    "eligible_sources_seen",
    "eligible_neighbors_found",
    "unavailable_opportunities",
    "requests_accepted",
]

RAW_FIELDS = [
    "component",
    "scenario",
    "factor",
    "level",
    "accounting",
    "r",
    "replicate",
    "master_seed",
    "initialization_signature",
    "network_type",
    "market_sociality",
    "fit_mean",
    "status_mean",
    "uncertainty_mean",
    "beta_0",
    "beta_individual",
    "beta_social",
    "budget_limit",
    "seed_adopters",
    *[f"direct_{name}" for name in PROCESS_FIELDS],
    *[f"referral_{name}" for name in PROCESS_FIELDS],
    "delta_adoptions",
]

SUMMARY_MEAN_FIELDS = [
    field_name
    for field_name in RAW_FIELDS
    if field_name.startswith("direct_") or field_name.startswith("referral_")
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def quantile(values: list[float], probability: float) -> float:
    if not values:
        return float("nan")
    return float(np.quantile(np.asarray(values, dtype=float), probability))


def mean_to_beta(mean: float, concentration: float = 10.0) -> tuple[float, float]:
    if not 0.0 < mean < 1.0:
        raise ValueError("beta-distribution mean must be in (0,1)")
    return mean * concentration, (1.0 - mean) * concentration


def map_updates(updates: dict[str, Any]) -> dict[str, Any]:
    mapped = dict(updates)
    status_mean = mapped.pop("status_mean", None)
    uncertainty_mean = mapped.pop("uncertainty_mean", None)
    if status_mean is not None:
        mapped["status_alpha"], mapped["status_beta"] = mean_to_beta(
            float(status_mean)
        )
    if uncertainty_mean is not None:
        mapped["uncertainty_alpha"], mapped["uncertainty_beta"] = mean_to_beta(
            float(uncertainty_mean)
        )
    if "seed_adopters" in mapped:
        mapped["seed_adopters"] = int(mapped["seed_adopters"])
    if "budget_limit" in mapped:
        mapped["budget_limit"] = float(mapped["budget_limit"])
    return mapped


def _extract(summary: dict[str, Any], name: str) -> float | int | str:
    value = summary[name]
    if value == "":
        return ""
    return value


def paired_worker(
    payload: tuple[
        str,
        dict[str, Any],
        str,
        int,
        list[float],
        int,
    ]
) -> list[dict[str, Any]]:
    component, scenario, accounting, replicate, r_grid, experiment_seed = payload
    paired_seed = stable_seed(
        experiment_seed, "main_study_v0.5", component, scenario["scenario"], replicate
    )
    updates = map_updates(dict(scenario["updates"]))
    common = {
        **BASE,
        **updates,
        "cost_accounting": accounting,
        "master_seed": paired_seed,
        "replicate_id": replicate,
    }
    direct_result = EntrepreneurialNetworkActivationModel(
        ModelConfig.from_dict({**common, "strategy": "direct"})
    ).run()
    direct = direct_result.summary
    rows: list[dict[str, Any]] = []
    for relative_cost in r_grid:
        referral_result = EntrepreneurialNetworkActivationModel(
            ModelConfig.from_dict(
                {
                    **common,
                    "strategy": "referral",
                    "referral_action_cost": float(relative_cost),
                }
            )
        ).run()
        if (
            direct_result.initialization_signature
            != referral_result.initialization_signature
        ):
            raise AssertionError("paired initialization failed")
        referral = referral_result.summary
        row: dict[str, Any] = {
            "component": component,
            "scenario": scenario["scenario"],
            "factor": scenario.get("factor", component),
            "level": scenario.get("level", scenario["scenario"]),
            "accounting": accounting,
            "r": float(relative_cost),
            "replicate": replicate,
            "master_seed": paired_seed,
            "initialization_signature": direct_result.initialization_signature,
            "network_type": common["network_type"],
            "market_sociality": common["market_sociality"],
            "fit_mean": common["fit_mean"],
            "status_mean": (
                common["status_alpha"]
                / (common["status_alpha"] + common["status_beta"])
            ),
            "uncertainty_mean": (
                common["uncertainty_alpha"]
                / (common["uncertainty_alpha"] + common["uncertainty_beta"])
            ),
            "beta_0": common["beta_0"],
            "beta_individual": common["beta_individual"],
            "beta_social": common["beta_social"],
            "budget_limit": common["budget_limit"],
            "seed_adopters": common["seed_adopters"],
        }
        for field_name in PROCESS_FIELDS:
            row[f"direct_{field_name}"] = _extract(direct, field_name)
            row[f"referral_{field_name}"] = _extract(referral, field_name)
        row["delta_adoptions"] = (
            float(referral["new_adoptions"]) - float(direct["new_adoptions"])
        )
        rows.append(row)
    return rows


@dataclass
class CellAccumulator:
    meta: dict[str, Any]
    deltas: list[float] = field(default_factory=list)
    sums: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add(self, row: dict[str, Any]) -> None:
        self.deltas.append(float(row["delta_adoptions"]))
        for name in SUMMARY_MEAN_FIELDS:
            value = row[name]
            if value == "":
                continue
            self.sums[name] += float(value)
            self.counts[name] += 1

    def summary(self) -> dict[str, Any]:
        differences = self.deltas
        mean_delta = statistics.fmean(differences)
        sd_delta = statistics.stdev(differences) if len(differences) > 1 else 0.0
        mcse = sd_delta / math.sqrt(len(differences))
        result = {
            **self.meta,
            "replicates": len(differences),
            "mean_delta": mean_delta,
            "sd_delta": sd_delta,
            "mcse_delta": mcse,
            "ci95_lower": mean_delta - Z_975 * mcse,
            "ci95_upper": mean_delta + Z_975 * mcse,
            "median_delta": statistics.median(differences),
            "p10_delta": quantile(differences, 0.10),
            "p90_delta": quantile(differences, 0.90),
            "probability_referral_higher": statistics.fmean(
                value > 0 for value in differences
            ),
            "probability_equal": statistics.fmean(
                value == 0 for value in differences
            ),
            "probability_referral_not_lower": statistics.fmean(
                value >= 0 for value in differences
            ),
            "mean_delta_allocated_efficiency": (
                mean_delta / float(self.meta["budget_limit"])
                if float(self.meta["budget_limit"])
                else 0.0
            ),
        }
        for name in SUMMARY_MEAN_FIELDS:
            count = self.counts[name]
            result[f"mean_{name}"] = self.sums[name] / count if count else ""
        return result


def deterministic_lhs_profiles(
    design: dict[str, Any], experiment_seed: int
) -> list[dict[str, Any]]:
    count = int(design["profiles"])
    ranges = design["parameter_ranges"]
    rng = random.Random(stable_seed(experiment_seed, "lhs_design"))
    columns: dict[str, list[float]] = {}
    for name, (low, high) in ranges.items():
        strata = list(range(count))
        rng.shuffle(strata)
        columns[name] = [
            float(low) + ((stratum + 0.5) / count) * (float(high) - float(low))
            for stratum in strata
        ]
    networks = list(design["network_types"])
    if count % len(networks):
        raise ValueError("profile count must be divisible by network count")
    assigned = [network for network in networks for _ in range(count // len(networks))]
    rng.shuffle(assigned)
    profiles: list[dict[str, Any]] = []
    for index in range(count):
        updates: dict[str, Any] = {
            name: columns[name][index] for name in ranges
        }
        updates["budget_limit"] = int(round(updates["budget_limit"]))
        updates["seed_adopters"] = int(round(updates["seed_adopters"]))
        updates["network_type"] = assigned[index]
        profiles.append(
            {
                "scenario": f"P{index + 1:03d}",
                "factor": "main_lhs_profile",
                "level": f"profile_{index + 1:03d}",
                "updates": updates,
            }
        )
    return profiles


def profile_rows(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        rows.append({"profile": profile["scenario"], **profile["updates"]})
    return rows


def _raw_writer(path: Path, append: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    binary = path.open("ab" if append else "wb")
    compressed = gzip.GzipFile(
        filename="",
        mode="wb",
        fileobj=binary,
        mtime=0,
    )
    handle = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
    writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
    if not append:
        writer.writeheader()
    return handle, writer


def execute_tasks(
    *,
    component: str,
    scenarios: list[dict[str, Any]],
    accounting: str,
    replicates: int,
    r_by_scenario: dict[str, list[float]],
    experiment_seed: int,
    workers: int,
    raw_path: Path,
    accumulators: dict[tuple[str, str, float], CellAccumulator],
    append: bool,
) -> int:
    tasks = [
        (
            component,
            scenario,
            accounting,
            replicate,
            r_by_scenario.get(scenario["scenario"], []),
            experiment_seed,
        )
        for scenario in scenarios
        for replicate in range(replicates)
        if r_by_scenario.get(scenario["scenario"])
    ]
    scenario_lookup = {scenario["scenario"]: scenario for scenario in scenarios}
    row_count = 0
    handle, writer = _raw_writer(raw_path, append=append)
    try:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for result_rows in executor.map(paired_worker, tasks, chunksize=2):
                for row in result_rows:
                    writer.writerow(row)
                    row_count += 1
                    key = (
                        str(row["scenario"]),
                        str(row["accounting"]),
                        float(row["r"]),
                    )
                    if key not in accumulators:
                        scenario = scenario_lookup[str(row["scenario"])]
                        accumulators[key] = CellAccumulator(
                            {
                                "scenario": row["scenario"],
                                "factor": row["factor"],
                                "level": row["level"],
                                "accounting": row["accounting"],
                                "r": float(row["r"]),
                                "network_type": row["network_type"],
                                "market_sociality": row["market_sociality"],
                                "fit_mean": row["fit_mean"],
                                "status_mean": row["status_mean"],
                                "uncertainty_mean": row["uncertainty_mean"],
                                "beta_0": row["beta_0"],
                                "beta_individual": row["beta_individual"],
                                "beta_social": row["beta_social"],
                                "budget_limit": row["budget_limit"],
                                "seed_adopters": row["seed_adopters"],
                                "description": scenario.get("description", ""),
                            }
                        )
                    accumulators[key].add(row)
    finally:
        handle.close()
    return row_count


def run_refined_grid(
    *,
    component: str,
    scenarios: list[dict[str, Any]],
    accounting: str,
    replicates: int,
    coarse_grid: list[float],
    tolerance: float,
    experiment_seed: int,
    workers: int,
    raw_path: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[tuple[str, str, float], CellAccumulator],
    int,
]:
    accumulators: dict[tuple[str, str, float], CellAccumulator] = {}
    coarse_rows = execute_tasks(
        component=component,
        scenarios=scenarios,
        accounting=accounting,
        replicates=replicates,
        r_by_scenario={
            scenario["scenario"]: coarse_grid for scenario in scenarios
        },
        experiment_seed=experiment_seed,
        workers=workers,
        raw_path=raw_path,
        accumulators=accumulators,
        append=False,
    )
    coarse_summaries = [
        accumulator.summary() for accumulator in accumulators.values()
    ]
    refinements = refinement_grid(
        coarse_summaries,
        tolerance=tolerance,
        lower_bound=min(coarse_grid),
        upper_bound=max(coarse_grid),
    )
    refinement_by_scenario = {
        scenario["scenario"]: refinements.get(
            (scenario["scenario"], accounting), []
        )
        for scenario in scenarios
    }
    refined_rows = execute_tasks(
        component=component,
        scenarios=scenarios,
        accounting=accounting,
        replicates=replicates,
        r_by_scenario=refinement_by_scenario,
        experiment_seed=experiment_seed,
        workers=workers,
        raw_path=raw_path,
        accumulators=accumulators,
        append=True,
    )
    summaries = sorted(
        (accumulator.summary() for accumulator in accumulators.values()),
        key=lambda row: (
            str(row["scenario"]),
            str(row["accounting"]),
            float(row["r"]),
        ),
    )
    thresholds = threshold_summary(summaries)
    return summaries, thresholds, accumulators, coarse_rows + refined_rows


def bootstrap_thresholds(
    accumulators: dict[tuple[str, str, float], CellAccumulator],
    *,
    bootstraps: int,
    experiment_seed: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[tuple[float, list[float]]]] = defaultdict(list)
    for (scenario, accounting, relative_cost), accumulator in accumulators.items():
        grouped[(scenario, accounting)].append((relative_cost, accumulator.deltas))
    output: list[dict[str, Any]] = []
    for (scenario, accounting), cells in sorted(grouped.items()):
        ordered = sorted(cells)
        r_values = np.asarray([cell[0] for cell in ordered], dtype=float)
        matrix = np.asarray([cell[1] for cell in ordered], dtype=float).T
        replicate_count = matrix.shape[0]
        rng = np.random.default_rng(
            stable_seed(experiment_seed, "threshold_bootstrap", scenario, accounting)
        )
        thresholds: list[float] = []
        no_competitive = 0
        upper = 0
        for _ in range(bootstraps):
            indices = rng.integers(0, replicate_count, size=replicate_count)
            means = matrix[indices].mean(axis=0)
            competitive = r_values[means >= 0]
            if not len(competitive):
                no_competitive += 1
                continue
            threshold = float(competitive.max())
            thresholds.append(threshold)
            upper += int(threshold == float(r_values.max()))
        output.append(
            {
                "scenario": scenario,
                "accounting": accounting,
                "bootstraps": bootstraps,
                "finite_threshold_bootstraps": len(thresholds),
                "probability_no_competitive_region": no_competitive / bootstraps,
                "probability_competitive_through_upper_bound": upper / bootstraps,
                "bootstrap_mean_r_star": (
                    statistics.fmean(thresholds) if thresholds else ""
                ),
                "bootstrap_median_r_star": (
                    statistics.median(thresholds) if thresholds else ""
                ),
                "bootstrap_r_star_p025": (
                    quantile(thresholds, 0.025) if thresholds else ""
                ),
                "bootstrap_r_star_p975": (
                    quantile(thresholds, 0.975) if thresholds else ""
                ),
                "bootstrap_interval_width": (
                    quantile(thresholds, 0.975) - quantile(thresholds, 0.025)
                    if thresholds
                    else ""
                ),
            }
        )
    return output


def baseline_scenario(
    scenario: str,
    updates: dict[str, Any],
    factor: str,
    level: str,
    description: str,
) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "factor": factor,
        "level": level,
        "description": description,
        "updates": updates,
    }


def process_scenarios(config: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for network in config["process_robustness"]["contexts"]:
        for regime, updates in config["process_robustness"]["regimes"].items():
            output.append(
                baseline_scenario(
                    f"process__{network}__{regime}",
                    {"network_type": network, **updates},
                    "exposure_process",
                    f"{network}:{regime}",
                    "Predeclared exposure-process robustness regime.",
                )
            )
    return output


def context_scenarios(
    contexts: dict[str, dict[str, Any]], component: str
) -> list[dict[str, Any]]:
    return [
        baseline_scenario(
            f"{component}__{name}",
            updates,
            component,
            name,
            f"Predeclared {component.replace('_', ' ')} context.",
        )
        for name, updates in contexts.items()
    ]


def exact_cost_summary(
    summaries: list[dict[str, Any]], relative_cost: float
) -> list[dict[str, Any]]:
    return [
        row for row in summaries if abs(float(row["r"]) - relative_cost) < 1e-9
    ]


def merge_threshold_features(
    thresholds: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lookup = {profile["scenario"]: profile["updates"] for profile in profiles}
    output: list[dict[str, Any]] = []
    for row in thresholds:
        output.append({**row, **lookup[str(row["scenario"])]})
    return output


def sensitivity_analysis(
    output_dir: Path,
    thresholds: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    fixed_120_summaries: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    experiment_seed: int,
) -> dict[str, Any]:
    from scipy.stats import spearmanr
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import permutation_importance
    from sklearn.metrics import accuracy_score, r2_score
    from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    from sklearn.tree import DecisionTreeClassifier, export_text

    features = merge_threshold_features(thresholds, profiles)
    finite = [
        row
        for row in features
        if row["r_star_primary_grid"] != ""
        and int(row["interpretable_single_threshold"]) == 1
    ]
    continuous = [
        "market_sociality",
        "fit_mean",
        "status_mean",
        "uncertainty_mean",
        "beta_0",
        "beta_individual",
        "beta_social",
        "budget_limit",
        "seed_adopters",
    ]
    spearman_rows: list[dict[str, Any]] = []
    y = np.asarray([float(row["r_star_primary_grid"]) for row in finite])
    for name in continuous:
        x = np.asarray([float(row[name]) for row in finite])
        rho, p_value = spearmanr(x, y)
        spearman_rows.append(
            {
                "parameter": name,
                "finite_profiles": len(finite),
                "spearman_rho": float(rho),
                "two_sided_p_value_descriptive_only": float(p_value),
            }
        )
    write_csv(output_dir / "sensitivity_spearman_v0.5.csv", spearman_rows)

    feature_names = continuous + ["network_type"]
    X = [{name: row[name] for name in feature_names} for row in finite]
    import pandas as pd

    frame = pd.DataFrame(X)
    preprocess = ColumnTransformer(
        [
            ("continuous", StandardScaler(), continuous),
            (
                "network",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["network_type"],
            ),
        ]
    )
    forest = RandomForestRegressor(
        n_estimators=600,
        min_samples_leaf=4,
        max_features=0.75,
        random_state=experiment_seed,
        n_jobs=1,
    )
    pipeline = Pipeline([("preprocess", preprocess), ("model", forest)])
    folds = KFold(n_splits=5, shuffle=True, random_state=experiment_seed)
    cv_scores = cross_val_score(pipeline, frame, y, cv=folds, scoring="r2")
    pipeline.fit(frame, y)
    transformed = pipeline.named_steps["preprocess"].transform(frame)
    transformed_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    importance = permutation_importance(
        pipeline.named_steps["model"],
        transformed,
        y,
        scoring="r2",
        n_repeats=100,
        random_state=experiment_seed,
        n_jobs=1,
    )
    importance_rows = [
        {
            "encoded_parameter": str(name),
            "importance_mean_r2_decrease": float(mean),
            "importance_sd": float(sd),
        }
        for name, mean, sd in sorted(
            zip(
                transformed_names,
                importance.importances_mean,
                importance.importances_std,
            ),
            key=lambda item: item[1],
            reverse=True,
        )
    ]
    write_csv(output_dir / "sensitivity_permutation_importance_v0.5.csv", importance_rows)

    curve_lookup = {
        (str(row["scenario"]), float(row["r"])): row for row in summaries
    }
    curve_lookup.update(
        {
            (str(row["scenario"]), float(row["r"])): row
            for row in fixed_120_summaries
        }
    )
    classification_results: dict[str, Any] = {}
    rule_sections = [
        "# Descriptive competitiveness rules v0.5",
        "",
        "These shallow-tree rules summarize simulated profiles. They are not",
        "causal claims or empirically estimated decision rules.",
        "",
    ]
    for relative_cost in (1.0, 1.2):
        class_rows = [
            {
                **profile["updates"],
                "scenario": profile["scenario"],
                "competitive": int(
                    float(curve_lookup[(profile["scenario"], relative_cost)]["mean_delta"])
                    >= 0
                ),
            }
            for profile in profiles
        ]
        class_frame = pd.DataFrame(
            [{name: row[name] for name in feature_names} for row in class_rows]
        )
        labels = np.asarray([row["competitive"] for row in class_rows])
        class_preprocess = ColumnTransformer(
            [
                ("continuous", StandardScaler(), continuous),
                (
                    "network",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    ["network_type"],
                ),
            ]
        )
        tree = DecisionTreeClassifier(
            max_depth=3,
            min_samples_leaf=8,
            class_weight="balanced",
            random_state=experiment_seed,
        )
        class_pipeline = Pipeline(
            [("preprocess", class_preprocess), ("model", tree)]
        )
        if len(set(labels)) > 1 and min(np.bincount(labels)) >= 5:
            splits = min(5, int(min(np.bincount(labels))))
            cv = StratifiedKFold(
                n_splits=splits, shuffle=True, random_state=experiment_seed
            )
            accuracy = float(
                cross_val_score(
                    class_pipeline, class_frame, labels, cv=cv, scoring="accuracy"
                ).mean()
            )
        else:
            accuracy = float("nan")
        class_pipeline.fit(class_frame, labels)
        transformed_names = (
            class_pipeline.named_steps["preprocess"].get_feature_names_out()
        )
        rules = export_text(
            class_pipeline.named_steps["model"],
            feature_names=list(transformed_names),
            decimals=3,
        )
        predictions = class_pipeline.predict(class_frame)
        classification_results[f"r_{relative_cost:.2f}"] = {
            "competitive_profiles": int(labels.sum()),
            "profiles": len(labels),
            "competitive_share": float(labels.mean()),
            "cross_validated_accuracy": accuracy,
            "training_accuracy": float(accuracy_score(labels, predictions)),
        }
        rule_sections.extend(
            [
                f"## Relative cost r={relative_cost:.2f}",
                "",
                "```text",
                rules.rstrip(),
                "```",
                "",
            ]
        )
    (output_dir / "competitiveness_rules_v0.5.md").write_text(
        "\n".join(rule_sections) + "\n", encoding="utf-8"
    )
    return {
        "finite_profiles": len(finite),
        "forest_cv_r2_mean": float(np.mean(cv_scores)),
        "forest_cv_r2_sd": float(np.std(cv_scores, ddof=1)),
        "classification": classification_results,
    }


def summarize_threshold_distribution(
    thresholds: list[dict[str, Any]],
    bootstraps: list[dict[str, Any]],
) -> dict[str, Any]:
    finite = [
        row
        for row in thresholds
        if row["r_star_primary_grid"] != ""
        and int(row["interpretable_single_threshold"]) == 1
    ]
    values = [float(row["r_star_primary_grid"]) for row in finite]
    widths = [
        float(row["bootstrap_interval_width"])
        for row in bootstraps
        if row["bootstrap_interval_width"] != ""
    ]
    return {
        "profiles": len(thresholds),
        "finite_interpretable_profiles": len(finite),
        "finite_share": len(finite) / len(thresholds),
        "r_star_min": min(values) if values else "",
        "r_star_p25": quantile(values, 0.25) if values else "",
        "r_star_median": statistics.median(values) if values else "",
        "r_star_p75": quantile(values, 0.75) if values else "",
        "r_star_max": max(values) if values else "",
        "multiple_crossing_profiles": sum(
            int(row["crossing_count"]) > 1 for row in thresholds
        ),
        "no_competitive_profiles": sum(
            row["r_star_primary_grid"] == "" for row in thresholds
        ),
        "upper_boundary_profiles": sum(
            int(row["competitive_through_upper_bound"]) == 1
            for row in thresholds
        ),
        "median_bootstrap_width": statistics.median(widths) if widths else "",
        "bootstrap_width_over_0_50_share": (
            statistics.fmean(width > 0.50 for width in widths) if widths else ""
        ),
    }


def network_threshold_summary(
    thresholds: list[dict[str, Any]], profiles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    lookup = {profile["scenario"]: profile["updates"] for profile in profiles}
    grouped: dict[str, list[float]] = defaultdict(list)
    totals: dict[str, int] = defaultdict(int)
    for row in thresholds:
        network = str(lookup[str(row["scenario"])]["network_type"])
        totals[network] += 1
        if (
            row["r_star_primary_grid"] != ""
            and int(row["interpretable_single_threshold"]) == 1
        ):
            grouped[network].append(float(row["r_star_primary_grid"]))
    rows: list[dict[str, Any]] = []
    for network in sorted(totals):
        values = grouped[network]
        rows.append(
            {
                "network_type": network,
                "profiles": totals[network],
                "finite_profiles": len(values),
                "finite_share": len(values) / totals[network],
                "r_star_median": statistics.median(values) if values else "",
                "r_star_p25": quantile(values, 0.25) if values else "",
                "r_star_p75": quantile(values, 0.75) if values else "",
                "r_star_min": min(values) if values else "",
                "r_star_max": max(values) if values else "",
            }
        )
    return rows


def accounting_comparison(
    upfront: list[dict[str, Any]], staged: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    left = {str(row["scenario"]): row for row in upfront}
    right = {str(row["scenario"]): row for row in staged}
    output: list[dict[str, Any]] = []
    for scenario in sorted(set(left) & set(right)):
        u = left[scenario]
        s = right[scenario]
        u_value = u["r_star_primary_grid"]
        s_value = s["r_star_primary_grid"]
        difference: float | str = ""
        if u_value != "" and s_value != "":
            difference = float(s_value) - float(u_value)
        output.append(
            {
                "scenario": scenario,
                "upfront_r_star": u_value,
                "staged_r_star": s_value,
                "staged_minus_upfront": difference,
                "absolute_difference_at_least_0_25": int(
                    difference != "" and abs(float(difference)) >= 0.25
                ),
                "upfront_interpretable": u["interpretable_single_threshold"],
                "staged_interpretable": s["interpretable_single_threshold"],
            }
        )
    return output


def dynamic_robustness_scenarios(config: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for takeoff in config["dynamic_robustness"]["takeoff_shares"]:
        for quiet in config["dynamic_robustness"]["quiet_periods"]:
            output.append(
                baseline_scenario(
                    f"dynamic__takeoff_{takeoff:.2f}__quiet_{quiet}",
                    {"takeoff_share": takeoff, "quiet_period": quiet},
                    "dynamic_definition",
                    f"takeoff={takeoff:.2f};quiet={quiet}",
                    "Alternative takeoff and extinction definition.",
                )
            )
    return output


def make_figures(
    output_dir: Path,
    thresholds: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    process_thresholds: list[dict[str, Any]],
    importance_rows: list[dict[str, Any]],
) -> None:
    import matplotlib.pyplot as plt

    merged = merge_threshold_features(thresholds, profiles)
    finite = [
        row
        for row in merged
        if row["r_star_primary_grid"] != ""
        and int(row["interpretable_single_threshold"]) == 1
    ]
    colors = {
        "ring": "#8f5b34",
        "small_world": "#386a8f",
        "preferential_attachment": "#4d8b55",
    }
    markers = {"ring": "o", "small_world": "s", "preferential_attachment": "^"}

    figure, axis = plt.subplots(figsize=(9, 6))
    for network in colors:
        selected = [row for row in finite if row["network_type"] == network]
        scatter = axis.scatter(
            [float(row["market_sociality"]) for row in selected],
            [float(row["budget_limit"]) for row in selected],
            c=[float(row["r_star_primary_grid"]) for row in selected],
            cmap="viridis",
            vmin=0.25,
            vmax=3.0,
            marker=markers[network],
            edgecolor="black",
            linewidth=0.4,
            s=65,
            label=network.replace("_", " "),
        )
    axis.set_xlabel("Market sociality (diagnostic)")
    axis.set_ylabel("Allocated budget units")
    axis.set_title("Profile-specific referral cost thresholds")
    axis.legend()
    figure.colorbar(scatter, ax=axis, label="Primary r*")
    figure.tight_layout()
    figure.savefig(
        output_dir / "figure_r_star_profile_map_v0.5.png",
        dpi=180,
        metadata={"Software": "ENA ABM v0.5"},
    )
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 5))
    network_values = [
        [
            float(row["r_star_primary_grid"])
            for row in finite
            if row["network_type"] == network
        ]
        for network in ("ring", "small_world", "preferential_attachment")
    ]
    axis.boxplot(
        network_values,
        tick_labels=["Ring", "Small world", "Preferential attachment"],
        showfliers=True,
    )
    axis.axhline(1.0, linestyle="--", color="#333333", linewidth=1)
    axis.set_ylabel("Primary r*")
    axis.set_title("Threshold distribution by network structure")
    figure.tight_layout()
    figure.savefig(
        output_dir / "figure_r_star_by_network_v0.5.png",
        dpi=180,
        metadata={"Software": "ENA ABM v0.5"},
    )
    plt.close(figure)

    selected_importance = importance_rows[:12]
    figure, axis = plt.subplots(figsize=(9, 6))
    labels = [
        str(row["encoded_parameter"]).replace("continuous__", "").replace(
            "network__", ""
        )
        for row in reversed(selected_importance)
    ]
    values = [
        float(row["importance_mean_r2_decrease"])
        for row in reversed(selected_importance)
    ]
    errors = [float(row["importance_sd"]) for row in reversed(selected_importance)]
    axis.barh(labels, values, xerr=errors, color="#596f8f", alpha=0.9)
    axis.set_xlabel("Permutation decrease in emulator R²")
    axis.set_title("Nonlinear sensitivity of profile-specific r*")
    figure.tight_layout()
    figure.savefig(
        output_dir / "figure_sensitivity_importance_v0.5.png",
        dpi=180,
        metadata={"Software": "ENA ABM v0.5"},
    )
    plt.close(figure)

    process_rows = [
        row
        for row in process_thresholds
        if row["r_star_primary_grid"] != ""
        and int(row["interpretable_single_threshold"]) == 1
    ]
    process_rows.sort(key=lambda row: float(row["r_star_primary_grid"]))
    figure_height = max(7.0, len(process_rows) * 0.26)
    figure, axis = plt.subplots(figsize=(10, figure_height))
    axis.barh(
        list(range(len(process_rows))),
        [float(row["r_star_primary_grid"]) for row in process_rows],
        color="#627f59",
    )
    axis.set_yticks(list(range(len(process_rows))))
    axis.set_yticklabels(
        [str(row["level"]).replace("_", " ") for row in process_rows],
        fontsize=8,
    )
    axis.axvline(1.0, linestyle="--", color="#333333", linewidth=1)
    axis.set_xlabel("Primary r*")
    axis.set_title("Exposure-process robustness")
    figure.tight_layout()
    figure.savefig(
        output_dir / "figure_process_robustness_v0.5.png",
        dpi=180,
        metadata={"Software": "ENA ABM v0.5"},
    )
    plt.close(figure)


def stopping_diagnostics(
    config: dict[str, Any],
    distribution: dict[str, Any],
    thresholds: list[dict[str, Any]],
    accounting_rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    rules = config["stopping_rules"]
    multiple_share = (
        distribution["multiple_crossing_profiles"] / distribution["profiles"]
    )
    finite_share = distribution["finite_share"]
    wide_share = distribution["bootstrap_width_over_0_50_share"]
    residual_shares: list[float] = []
    for row in summaries:
        budget = float(row["budget_limit"])
        unused = row.get("mean_referral_unused_budget", "")
        if budget and unused != "":
            residual_shares.append(float(unused) / budget)
    rounding_material_share = (
        statistics.fmean(
            value >= float(rules["budget_rounding_share_material"])
            for value in residual_shares
        )
        if residual_shares
        else 0.0
    )
    accounting_material = sum(
        int(row["absolute_difference_at_least_0_25"]) for row in accounting_rows
    )
    accounting_reversal_blocker = accounting_material >= math.ceil(
        len(accounting_rows) / 2
    )
    blockers = {
        "multiple_crossings": multiple_share
        > float(rules["multiple_crossing_share_max"]),
        "insufficient_interpretable_profiles": finite_share
        < float(rules["minimum_interpretable_profile_share"]),
        "widespread_threshold_instability": wide_share > 0.50,
        "budget_rounding_dominance": rounding_material_share > 0.50,
        "accounting_convention_reverses_central_conclusion": (
            accounting_reversal_blocker
        ),
    }
    return {
        "multiple_crossing_share": multiple_share,
        "finite_interpretable_share": finite_share,
        "bootstrap_width_over_0_50_share": wide_share,
        "rounding_residual_over_limit_share_all_cells": rounding_material_share,
        "material_accounting_contexts": accounting_material,
        "accounting_contexts": len(accounting_rows),
        "blockers": blockers,
        "interpretation_blocked": any(blockers.values()),
    }


def markdown_report(
    output_dir: Path,
    config: dict[str, Any],
    distribution: dict[str, Any],
    network_rows: list[dict[str, Any]],
    sensitivity: dict[str, Any],
    exact_100: list[dict[str, Any]],
    exact_120: list[dict[str, Any]],
    process_thresholds: list[dict[str, Any]],
    accounting_rows: list[dict[str, Any]],
    structural_thresholds: list[dict[str, Any]],
    dynamic_summaries: list[dict[str, Any]],
    stop: dict[str, Any],
    total_rows: int,
) -> None:
    def aggregate_cost(rows: list[dict[str, Any]]) -> dict[str, float]:
        return {
            "competitive_share": statistics.fmean(
                float(row["mean_delta"]) >= 0 for row in rows
            ),
            "mean_delta": statistics.fmean(float(row["mean_delta"]) for row in rows),
            "median_delta": statistics.median(
                float(row["mean_delta"]) for row in rows
            ),
            "mean_direct": statistics.fmean(
                float(row["mean_direct_new_adoptions"]) for row in rows
            ),
            "mean_referral": statistics.fmean(
                float(row["mean_referral_new_adoptions"]) for row in rows
            ),
        }

    at_100 = aggregate_cost(exact_100)
    at_120 = aggregate_cost(exact_120)
    process_no_region = [
        row["level"]
        for row in process_thresholds
        if row["r_star_primary_grid"] == ""
    ]
    accounting_differences = [
        abs(float(row["staged_minus_upfront"]))
        for row in accounting_rows
        if row["staged_minus_upfront"] != ""
    ]
    lines = [
        "# Main Simulation Study v0.5",
        "",
        "> Theoretical computational experiment. Parameters are diagnostic and",
        "> are not empirically calibrated.",
        "",
        "## Design",
        "",
        f"- {distribution['profiles']} stratified profiles.",
        f"- {config['replicates']} paired replications per profile-cost cell.",
        "- Three balanced network structures.",
        "- Relative referral cost searched from 0.25 to 3.00 and refined to 0.05.",
        f"- {total_rows:,} paired result rows across main and robustness analyses.",
        "",
        "## Main threshold distribution",
        "",
        f"- Interpretable finite thresholds: {distribution['finite_interpretable_profiles']}/{distribution['profiles']} "
        f"({distribution['finite_share']:.1%}).",
        f"- Median r*: {distribution['r_star_median']:.2f}.",
        f"- Interquartile range: [{distribution['r_star_p25']:.2f}, "
        f"{distribution['r_star_p75']:.2f}].",
        f"- Finite range: [{distribution['r_star_min']:.2f}, "
        f"{distribution['r_star_max']:.2f}].",
        f"- Multiple crossings: {distribution['multiple_crossing_profiles']}.",
        f"- No competitive tested region: {distribution['no_competitive_profiles']}.",
        f"- Median bootstrap interval width: "
        f"{distribution['median_bootstrap_width']:.2f}.",
        "",
        "## Equal-cost and v0.4-threshold comparisons",
        "",
        f"At r=1.00, referrals is competitive in {at_100['competitive_share']:.1%} "
        f"of profiles. Mean profile-level Δ is {at_100['mean_delta']:.2f} "
        f"adoptions (direct {at_100['mean_direct']:.2f}; referral "
        f"{at_100['mean_referral']:.2f}).",
        "",
        f"At r=1.20, referrals is competitive in {at_120['competitive_share']:.1%} "
        f"of profiles. Mean profile-level Δ is {at_120['mean_delta']:.2f} "
        f"adoptions (direct {at_120['mean_direct']:.2f}; referral "
        f"{at_120['mean_referral']:.2f}).",
        "",
        "These percentages describe the registered theoretical design space, not",
        "the prevalence of real markets.",
        "",
        "## Network structure",
        "",
        "| Network | Finite profiles | Median r* | IQR |",
        "|---|---:|---:|---:|",
    ]
    for row in network_rows:
        lines.append(
            f"| {row['network_type'].replace('_', ' ')} | "
            f"{row['finite_profiles']}/{row['profiles']} | "
            f"{float(row['r_star_median']):.2f} | "
            f"[{float(row['r_star_p25']):.2f}, {float(row['r_star_p75']):.2f}] |"
        )
    lines.extend(
        [
            "",
            "## Global sensitivity",
            "",
            f"The nonlinear threshold emulator used "
            f"{sensitivity['finite_profiles']} finite profiles. Five-fold "
            f"cross-validated R² was {sensitivity['forest_cv_r2_mean']:.2f} "
            f"(SD {sensitivity['forest_cv_r2_sd']:.2f}). Permutation importance",
            "and rank associations are reported in separate tables. These are",
            "descriptive model sensitivities, not causal estimates.",
            "",
            "## Robustness",
            "",
            f"Exposure-process conditions without a competitive tested region: "
            f"{', '.join(process_no_region) if process_no_region else 'none'}.",
            f"The median absolute staged-versus-upfront threshold difference was "
            f"{statistics.median(accounting_differences):.2f}; "
            f"{stop['material_accounting_contexts']}/{stop['accounting_contexts']} "
            "predeclared contexts differed by at least 0.25.",
            f"Structural robustness produced "
            f"{sum(row['r_star_primary_grid'] != '' for row in structural_thresholds)} "
            f"finite thresholds across {len(structural_thresholds)} contexts.",
            f"Dynamic-definition robustness evaluated {len(dynamic_summaries)} "
            "condition-cost cells; adoption counts are unaffected by these",
            "definitions, while takeoff and extinction labels vary as intended.",
            "",
            "## Interpretation gate",
            "",
            f"Interpretation blocked: **{str(stop['interpretation_blocked']).lower()}**.",
        ]
    )
    for name, value in stop["blockers"].items():
        lines.append(f"- {name.replace('_', ' ')}: {str(value).lower()}.")
    lines.extend(
        [
            "",
            "## Scientific conclusion",
            "",
            "Referrals is not unconditionally superior. Its relative advantage",
            "depends jointly on the cost ratio, market and consumer parameters,",
            "network structure, resource availability, and the probability that",
            "the referral chain produces an effective exposure. The model identifies",
            "conditional theoretical regions; empirical work would be required to",
            "locate real firms or markets inside those regions.",
        ]
    )
    (output_dir / "MAIN_SIMULATION_REPORT_v0.5.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    article_lines = [
        "# Article Results Package v0.5",
        "",
        "## Defensible result statements",
        "",
        f"1. Across the registered theoretical design, the median finite cost "
        f"threshold was {distribution['r_star_median']:.2f}, with an "
        f"interquartile range of [{distribution['r_star_p25']:.2f}, "
        f"{distribution['r_star_p75']:.2f}].",
        f"2. At equal attempt cost, referrals was competitive in "
        f"{at_100['competitive_share']:.1%} of registered profiles; at r=1.20, "
        f"the share was {at_120['competitive_share']:.1%}.",
        "3. The exposure chain and the availability of adopted sources remain",
        "necessary boundary conditions; cost alone does not determine advantage.",
        "4. Results are heterogeneous across network and behavioral profiles, so",
        "a universal strategy ranking is not supported.",
        "",
        "## Required caveat",
        "",
        "The parameter ranges are diagnostic theoretical values. Profile shares,",
        "thresholds, and effect magnitudes describe the simulated design space and",
        "must not be interpreted as empirical prevalence or calibrated predictions.",
        "",
        "## Files for drafting",
        "",
        "- `main_thresholds_v0.5.csv`",
        "- `main_curve_summary_v0.5.csv`",
        "- `main_threshold_bootstrap_v0.5.csv`",
        "- `network_threshold_summary_v0.5.csv`",
        "- `sensitivity_permutation_importance_v0.5.csv`",
        "- `sensitivity_spearman_v0.5.csv`",
        "- `process_robustness_thresholds_v0.5.csv`",
        "- `accounting_robustness_comparison_v0.5.csv`",
        "- `structural_robustness_thresholds_v0.5.csv`",
        "- four article-ready figures.",
    ]
    (output_dir / "ARTICLE_RESULTS_PACKAGE_v0.5.md").write_text(
        "\n".join(article_lines) + "\n", encoding="utf-8"
    )


def build_manifest(
    output_dir: Path,
    *,
    config_path: Path,
    design_hash: str,
    total_rows: int,
    interpretation_blocked: bool,
) -> None:
    principal = [
        path
        for path in sorted(output_dir.iterdir())
        if path.is_file()
        and path.name not in {"manifest_v0.5.json", "principal_hashes_v0.5.csv"}
        and path.suffix in {".csv", ".gz", ".json", ".md", ".png"}
    ]
    hash_rows = [
        {"file": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
        for path in principal
    ]
    write_csv(output_dir / "principal_hashes_v0.5.csv", hash_rows)
    manifest = {
        "scientific_status": "main_theoretical_simulation_diagnostic_parameters",
        "parameters_empirically_calibrated": False,
        "config_sha256": sha256(config_path),
        "pre_execution_design_sha256": design_hash,
        "total_paired_rows": total_rows,
        "interpretation_blocked": interpretation_blocked,
        "principal_files": len(hash_rows),
    }
    (output_dir / "manifest_v0.5.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--resume-main",
        action="store_true",
        help="Reuse a completed main grid, threshold table, and bootstrap.",
    )
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    experiment_seed = int(config["experiment_seed"])
    replicates = int(config["replicates"])
    coarse_grid = [float(value) for value in config["relative_cost"]["coarse_grid"]]
    tolerance = float(config["relative_cost"]["refinement_tolerance"])
    design_document = args.config.parent.parent / "docs" / "PREREGISTERED_DESIGN_v0.5.md"
    design_hash = sha256(design_document)

    profiles = deterministic_lhs_profiles(config["main_design"], experiment_seed)
    write_csv(args.output / "registered_profiles_v0.5.csv", profile_rows(profiles))
    (args.output / "pre_execution_registry_v0.5.json").write_text(
        json.dumps(
            {
                "config_sha256": sha256(args.config),
                "design_document_sha256": design_hash,
                "experiment_seed": experiment_seed,
                "profiles": len(profiles),
                "replicates": replicates,
                "coarse_grid": coarse_grid,
                "refinement_tolerance": tolerance,
                "parameters_empirically_calibrated": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    total_rows = 0
    if args.resume_main:
        required = [
            args.output / "main_paired_runs_v0.5.csv.gz",
            args.output / "main_curve_summary_v0.5.csv",
            args.output / "main_thresholds_v0.5.csv",
            args.output / "main_threshold_bootstrap_v0.5.csv",
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(
                "Cannot resume; missing completed main outputs: " + ", ".join(missing)
            )
        main_summaries = read_csv(
            args.output / "main_curve_summary_v0.5.csv"
        )
        main_thresholds = read_csv(args.output / "main_thresholds_v0.5.csv")
        main_bootstrap = read_csv(
            args.output / "main_threshold_bootstrap_v0.5.csv"
        )
        with gzip.open(
            args.output / "main_paired_runs_v0.5.csv.gz",
            "rt",
            encoding="utf-8",
            newline="",
        ) as handle:
            total_rows += sum(1 for _ in handle) - 1
    else:
        (
            main_summaries,
            main_thresholds,
            main_accumulators,
            rows,
        ) = run_refined_grid(
            component="main_design",
            scenarios=profiles,
            accounting=config["primary_accounting"],
            replicates=replicates,
            coarse_grid=coarse_grid,
            tolerance=tolerance,
            experiment_seed=experiment_seed,
            workers=args.workers,
            raw_path=args.output / "main_paired_runs_v0.5.csv.gz",
        )
        total_rows += rows
        write_csv(args.output / "main_curve_summary_v0.5.csv", main_summaries)
        enriched_thresholds = merge_threshold_features(main_thresholds, profiles)
        write_csv(args.output / "main_thresholds_v0.5.csv", enriched_thresholds)
        main_bootstrap = bootstrap_thresholds(
            main_accumulators,
            bootstraps=int(config["bootstrap_samples"]),
            experiment_seed=experiment_seed,
        )
        write_csv(
            args.output / "main_threshold_bootstrap_v0.5.csv",
            main_bootstrap,
        )
    distribution = summarize_threshold_distribution(
        main_thresholds, main_bootstrap
    )
    (args.output / "main_threshold_distribution_v0.5.json").write_text(
        json.dumps(distribution, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    network_rows = network_threshold_summary(main_thresholds, profiles)
    write_csv(args.output / "network_threshold_summary_v0.5.csv", network_rows)

    fixed_120_raw = args.output / "main_fixed_cost_1.20_runs_v0.5.csv.gz"
    fixed_120_summary_path = (
        args.output / "main_fixed_cost_1.20_summary_v0.5.csv"
    )
    if args.resume_main and fixed_120_raw.exists() and fixed_120_summary_path.exists():
        fixed_120_summaries = read_csv(fixed_120_summary_path)
        with gzip.open(
            fixed_120_raw, "rt", encoding="utf-8", newline=""
        ) as handle:
            total_rows += sum(1 for _ in handle) - 1
    else:
        fixed_120_accumulators: dict[
            tuple[str, str, float], CellAccumulator
        ] = {}
        rows = execute_tasks(
            component="main_design",
            scenarios=profiles,
            accounting=config["primary_accounting"],
            replicates=replicates,
            r_by_scenario={
                profile["scenario"]: [1.20] for profile in profiles
            },
            experiment_seed=experiment_seed,
            workers=args.workers,
            raw_path=fixed_120_raw,
            accumulators=fixed_120_accumulators,
            append=False,
        )
        total_rows += rows
        fixed_120_summaries = sorted(
            (
                accumulator.summary()
                for accumulator in fixed_120_accumulators.values()
            ),
            key=lambda row: str(row["scenario"]),
        )
        write_csv(fixed_120_summary_path, fixed_120_summaries)

    sensitivity = sensitivity_analysis(
        args.output,
        main_thresholds,
        main_summaries,
        fixed_120_summaries,
        profiles,
        experiment_seed,
    )
    (args.output / "sensitivity_manifest_v0.5.json").write_text(
        json.dumps(sensitivity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    process = process_scenarios(config)
    (
        process_summaries,
        process_thresholds,
        _,
        rows,
    ) = run_refined_grid(
        component="process_robustness",
        scenarios=process,
        accounting=config["primary_accounting"],
        replicates=replicates,
        coarse_grid=coarse_grid,
        tolerance=tolerance,
        experiment_seed=experiment_seed,
        workers=args.workers,
        raw_path=args.output / "process_robustness_runs_v0.5.csv.gz",
    )
    total_rows += rows
    write_csv(args.output / "process_robustness_curve_v0.5.csv", process_summaries)
    write_csv(
        args.output / "process_robustness_thresholds_v0.5.csv",
        process_thresholds,
    )

    accounting_contexts = context_scenarios(
        config["accounting_robustness_contexts"], "accounting"
    )
    (
        accounting_upfront_summaries,
        accounting_upfront_thresholds,
        _,
        rows,
    ) = run_refined_grid(
        component="accounting_robustness",
        scenarios=accounting_contexts,
        accounting=config["primary_accounting"],
        replicates=replicates,
        coarse_grid=coarse_grid,
        tolerance=tolerance,
        experiment_seed=experiment_seed,
        workers=args.workers,
        raw_path=args.output / "accounting_upfront_runs_v0.5.csv.gz",
    )
    total_rows += rows
    (
        accounting_staged_summaries,
        accounting_staged_thresholds,
        _,
        rows,
    ) = run_refined_grid(
        component="accounting_robustness",
        scenarios=accounting_contexts,
        accounting=config["secondary_accounting"],
        replicates=replicates,
        coarse_grid=coarse_grid,
        tolerance=tolerance,
        experiment_seed=experiment_seed,
        workers=args.workers,
        raw_path=args.output / "accounting_staged_runs_v0.5.csv.gz",
    )
    total_rows += rows
    accounting_rows = accounting_comparison(
        accounting_upfront_thresholds, accounting_staged_thresholds
    )
    write_csv(
        args.output / "accounting_robustness_comparison_v0.5.csv",
        accounting_rows,
    )
    write_csv(
        args.output / "accounting_upfront_curve_v0.5.csv",
        accounting_upfront_summaries,
    )
    write_csv(
        args.output / "accounting_staged_curve_v0.5.csv",
        accounting_staged_summaries,
    )

    structural = context_scenarios(
        config["structural_robustness_contexts"], "structural"
    )
    (
        structural_summaries,
        structural_thresholds,
        _,
        rows,
    ) = run_refined_grid(
        component="structural_robustness",
        scenarios=structural,
        accounting=config["primary_accounting"],
        replicates=replicates,
        coarse_grid=coarse_grid,
        tolerance=tolerance,
        experiment_seed=experiment_seed,
        workers=args.workers,
        raw_path=args.output / "structural_robustness_runs_v0.5.csv.gz",
    )
    total_rows += rows
    write_csv(
        args.output / "structural_robustness_curve_v0.5.csv",
        structural_summaries,
    )
    write_csv(
        args.output / "structural_robustness_thresholds_v0.5.csv",
        structural_thresholds,
    )

    dynamic = dynamic_robustness_scenarios(config)
    dynamic_accumulators: dict[tuple[str, str, float], CellAccumulator] = {}
    dynamic_r = [
        float(value)
        for value in config["dynamic_robustness"]["relative_cost_values"]
    ]
    rows = execute_tasks(
        component="dynamic_robustness",
        scenarios=dynamic,
        accounting=config["primary_accounting"],
        replicates=replicates,
        r_by_scenario={scenario["scenario"]: dynamic_r for scenario in dynamic},
        experiment_seed=experiment_seed,
        workers=args.workers,
        raw_path=args.output / "dynamic_robustness_runs_v0.5.csv.gz",
        accumulators=dynamic_accumulators,
        append=False,
    )
    total_rows += rows
    dynamic_summaries = sorted(
        (accumulator.summary() for accumulator in dynamic_accumulators.values()),
        key=lambda row: (str(row["scenario"]), float(row["r"])),
    )
    write_csv(
        args.output / "dynamic_robustness_summary_v0.5.csv",
        dynamic_summaries,
    )

    stop = stopping_diagnostics(
        config,
        distribution,
        main_thresholds,
        accounting_rows,
        main_summaries,
    )
    (args.output / "stopping_diagnostics_v0.5.json").write_text(
        json.dumps(stop, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    importance_rows: list[dict[str, Any]] = []
    with (args.output / "sensitivity_permutation_importance_v0.5.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        importance_rows = list(csv.DictReader(handle))
    make_figures(
        args.output,
        main_thresholds,
        profiles,
        process_thresholds,
        importance_rows,
    )
    markdown_report(
        args.output,
        config,
        distribution,
        network_rows,
        sensitivity,
        exact_cost_summary(main_summaries, 1.0),
        fixed_120_summaries,
        process_thresholds,
        accounting_rows,
        structural_thresholds,
        dynamic_summaries,
        stop,
        total_rows,
    )
    build_manifest(
        args.output,
        config_path=args.config,
        design_hash=design_hash,
        total_rows=total_rows,
        interpretation_blocked=bool(stop["interpretation_blocked"]),
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "output": str(args.output),
                "total_paired_rows": total_rows,
                "interpretation_blocked": stop["interpretation_blocked"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
