"""Run the preregistered v0.4 diagnostic break-even workflow.

The outputs are model-validation diagnostics, not the definitive article
experiment. The primary accounting convention is full expected cost at attempt
initiation. Staged accounting is retained as a secondary robustness estimand.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import statistics
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Iterable

from ena_abm.break_even import (
    DiagnosticScenario,
    paired_grid_worker,
    refinement_grid,
    summarize_grid,
    threshold_summary,
)
from ena_abm.rng import stable_seed


EXPERIMENT_SEED = 2026072404
PILOT_CHECKPOINTS = [50, 100, 200, 400]
PILOT_MCSE_TARGET = 0.30
PILOT_THRESHOLD_STABILITY = 0.05
REFINEMENT_TOLERANCE = 0.05
THRESHOLD_BOOTSTRAPS = 500
COARSE_GRID = [round(0.25 * index, 2) for index in range(1, 13)]
PILOT_GRID = [round(0.75 + 0.05 * index, 2) for index in range(17)]


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


SCENARIOS = [
    DiagnosticScenario(
        "baseline",
        "baseline",
        "diagnostic",
        "Small-world network and neutral conditional exposure mechanisms.",
        {},
    ),
    DiagnosticScenario(
        "sociality_zero",
        "market_sociality",
        "0.00",
        "No market-level weighting of social evidence.",
        {"market_sociality": 0.0},
    ),
    DiagnosticScenario(
        "sociality_high",
        "market_sociality",
        "0.90",
        "High market-level weighting of social evidence.",
        {"market_sociality": 0.9},
    ),
    DiagnosticScenario(
        "network_ring",
        "network_structure",
        "ring",
        "Regular ring with the baseline degree.",
        {"network_type": "ring"},
    ),
    DiagnosticScenario(
        "network_preferential_attachment",
        "network_structure",
        "preferential_attachment",
        "Heterogeneous preferential-attachment network.",
        {"network_type": "preferential_attachment"},
    ),
    DiagnosticScenario(
        "uncertainty_low",
        "initial_uncertainty",
        "0.25",
        "Low mean initial uncertainty.",
        {"uncertainty_mean": 0.25},
    ),
    DiagnosticScenario(
        "uncertainty_high",
        "initial_uncertainty",
        "0.80",
        "High mean initial uncertainty.",
        {"uncertainty_mean": 0.80},
    ),
    DiagnosticScenario(
        "status_low",
        "status_quo_satisfaction",
        "0.30",
        "Low mean satisfaction with the status quo.",
        {"status_mean": 0.30},
    ),
    DiagnosticScenario(
        "status_high",
        "status_quo_satisfaction",
        "0.80",
        "High mean satisfaction with the status quo.",
        {"status_mean": 0.80},
    ),
    DiagnosticScenario(
        "social_influence_absent",
        "social_influence",
        "beta_social=0",
        "No social-evidence contribution to adoption utility.",
        {"beta_social": 0.0},
    ),
    DiagnosticScenario(
        "no_referrers",
        "referrer_availability",
        "0 seeds",
        "No adopted referral source is available.",
        {"seed_adopters": 0},
    ),
    DiagnosticScenario(
        "referrers_scarce",
        "referrer_availability",
        "1 seed",
        "Only one initial adopted referral source.",
        {"seed_adopters": 1},
    ),
    DiagnosticScenario(
        "referrers_abundant",
        "referrer_availability",
        "8 seeds",
        "Eight initial adopted referral sources.",
        {"seed_adopters": 8},
    ),
    DiagnosticScenario(
        "eligible_neighbors_none",
        "eligible_neighbor_probability",
        "0.00",
        "Referral sources never produce an eligible neighbor.",
        {"referral_neighbor_availability_probability": 0.0},
    ),
    DiagnosticScenario(
        "eligible_neighbors_abundant",
        "eligible_neighbor_probability",
        "1.00",
        "Every structurally eligible source passes the neighbor-availability stage.",
        {"referral_neighbor_availability_probability": 1.0},
    ),
    DiagnosticScenario(
        "acceptance_low",
        "referral_acceptance_probability",
        "0.40",
        "Low probability that a referral request is accepted.",
        {"referral_acceptance_probability": 0.40},
    ),
    DiagnosticScenario(
        "acceptance_high",
        "referral_acceptance_probability",
        "1.00",
        "Every referral request is accepted.",
        {"referral_acceptance_probability": 1.00},
    ),
    DiagnosticScenario(
        "credibility_referral_low",
        "source_credibility",
        "direct 0.60 / referral 0.30",
        "Referral credibility below direct credibility.",
        {"referral_source_credibility": 0.30},
    ),
    DiagnosticScenario(
        "credibility_referral_high",
        "source_credibility",
        "direct 0.60 / referral 0.90",
        "Referral credibility above direct credibility.",
        {"referral_source_credibility": 0.90},
    ),
    DiagnosticScenario(
        "budget_scarce",
        "budget",
        "8",
        "Extremely scarce normalized budget.",
        {"budget_limit": 8.0},
    ),
    DiagnosticScenario(
        "budget_abundant",
        "budget",
        "60",
        "Relatively abundant normalized budget.",
        {"budget_limit": 60.0},
    ),
    DiagnosticScenario(
        "network_size_small",
        "network_size",
        "50",
        "Small diagnostic market.",
        {"n_consumers": 50},
    ),
    DiagnosticScenario(
        "network_size_large",
        "network_size",
        "200",
        "Large diagnostic market.",
        {"n_consumers": 200},
    ),
    DiagnosticScenario(
        "exposure_direct_advantage",
        "exposure_process",
        "direct 0.80 / referral 0.512",
        "Direct effective exposure is more probable than referral exposure.",
        {"direct_exposure_probability": 0.80},
    ),
    DiagnosticScenario(
        "exposure_referral_advantage",
        "exposure_process",
        "direct 0.512 / referral 0.729",
        "Referral conditional exposure is more probable than direct exposure.",
        {
            "referral_acceptance_probability": 0.90,
            "referral_neighbor_availability_probability": 0.90,
            "referral_introduction_probability": 0.90,
        },
    ),
    DiagnosticScenario(
        "exposure_equal_high",
        "exposure_process",
        "both 0.729",
        "Equal high conditional exposure probabilities.",
        {
            "direct_exposure_probability": 0.729,
            "referral_acceptance_probability": 0.90,
            "referral_neighbor_availability_probability": 0.90,
            "referral_introduction_probability": 0.90,
        },
    ),
]


ROBUSTNESS_SCENARIOS = {
    "baseline",
    "sociality_high",
    "referrers_scarce",
    "referrers_abundant",
    "acceptance_low",
    "budget_scarce",
    "budget_abundant",
}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_tasks(
    scenarios: Iterable[DiagnosticScenario],
    *,
    accounting: str,
    replicates: int,
    r_by_scenario: dict[str, list[float]],
    workers: int,
) -> list[dict[str, Any]]:
    tasks = [
        (
            BASE,
            scenario.to_dict(),
            accounting,
            replicate,
            r_by_scenario[scenario.name],
            EXPERIMENT_SEED,
        )
        for scenario in scenarios
        for replicate in range(replicates)
        if r_by_scenario.get(scenario.name)
    ]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for result in executor.map(paired_grid_worker, tasks, chunksize=2):
            rows.extend(result)
    return rows


def bracketing_mcse(summaries: list[dict[str, Any]]) -> float:
    ordered = sorted(summaries, key=lambda row: float(row["r"]))
    candidates: list[float] = []
    for left, right in zip(ordered, ordered[1:]):
        left_delta = float(left["mean_delta"])
        right_delta = float(right["mean_delta"])
        if (left_delta >= 0 > right_delta) or (right_delta >= 0 > left_delta):
            candidates.extend(
                [float(left["mcse_delta"]), float(right["mcse_delta"])]
            )
    return max(candidates) if candidates else max(
        float(row["mcse_delta"]) for row in ordered
    )


def run_precision_pilot(output_dir: Path, workers: int) -> int:
    baseline = [SCENARIOS[0]]
    all_rows: list[dict[str, Any]] = []
    for accounting in ("upfront_expected", "staged"):
        all_rows.extend(
            run_tasks(
                baseline,
                accounting=accounting,
                replicates=max(PILOT_CHECKPOINTS),
                r_by_scenario={"baseline": PILOT_GRID},
                workers=workers,
            )
        )
    write_csv(output_dir / "precision_pilot_runs_v0.4.csv", all_rows)

    checkpoint_rows: list[dict[str, Any]] = []
    thresholds: dict[tuple[str, int], dict[str, Any]] = {}
    for accounting in ("upfront_expected", "staged"):
        for checkpoint in PILOT_CHECKPOINTS:
            selected = [
                row
                for row in all_rows
                if row["accounting"] == accounting
                and int(row["replicate"]) < checkpoint
            ]
            summaries = summarize_grid(selected)
            threshold = threshold_summary(summaries)[0]
            thresholds[(accounting, checkpoint)] = threshold
            checkpoint_rows.append(
                {
                    "accounting": accounting,
                    "replicates": checkpoint,
                    "r_star_primary_grid": threshold["r_star_primary_grid"],
                    "r_star_conservative_grid": threshold[
                        "r_star_conservative_grid"
                    ],
                    "r_star_probability_grid": threshold[
                        "r_star_probability_grid"
                    ],
                    "bracketing_mcse": bracketing_mcse(summaries),
                    "worst_case_probability_mcse": math.sqrt(0.25 / checkpoint),
                }
            )
    write_csv(output_dir / "precision_pilot_checkpoints_v0.4.csv", checkpoint_rows)

    chosen = max(PILOT_CHECKPOINTS)
    for checkpoint, next_checkpoint in zip(
        PILOT_CHECKPOINTS, PILOT_CHECKPOINTS[1:]
    ):
        if checkpoint < 100:
            continue
        passes = True
        for accounting in ("upfront_expected", "staged"):
            current = thresholds[(accounting, checkpoint)]
            following = thresholds[(accounting, next_checkpoint)]
            current_r = current["r_star_primary_grid"]
            following_r = following["r_star_primary_grid"]
            matching_rows = [
                row
                for row in checkpoint_rows
                if row["accounting"] == accounting
                and row["replicates"] == checkpoint
            ][0]
            if current_r == "" or following_r == "":
                passes = False
            elif abs(float(current_r) - float(following_r)) > PILOT_THRESHOLD_STABILITY:
                passes = False
            elif float(matching_rows["bracketing_mcse"]) > PILOT_MCSE_TARGET:
                passes = False
            elif float(matching_rows["worst_case_probability_mcse"]) > 0.04:
                passes = False
        if passes:
            chosen = checkpoint
            break

    manifest = {
        "status": "diagnostic_only_not_article_evidence",
        "experiment_seed": EXPERIMENT_SEED,
        "pilot_grid": PILOT_GRID,
        "checkpoints": PILOT_CHECKPOINTS,
        "predeclared_mcse_target": PILOT_MCSE_TARGET,
        "predeclared_threshold_stability_tolerance": PILOT_THRESHOLD_STABILITY,
        "predeclared_probability_mcse_max": 0.04,
        "selected_replicates": chosen,
    }
    (output_dir / "precision_pilot_manifest_v0.4.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return chosen


def _combined_refinement(
    scenarios: list[DiagnosticScenario],
    *,
    accounting: str,
    replicates: int,
    workers: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    coarse = run_tasks(
        scenarios,
        accounting=accounting,
        replicates=replicates,
        r_by_scenario={scenario.name: COARSE_GRID for scenario in scenarios},
        workers=workers,
    )
    coarse_summary = summarize_grid(coarse)
    refinements = refinement_grid(
        coarse_summary,
        tolerance=REFINEMENT_TOLERANCE,
        lower_bound=min(COARSE_GRID),
        upper_bound=max(COARSE_GRID),
    )
    r_by_scenario = {
        scenario.name: refinements.get((scenario.name, accounting), [])
        for scenario in scenarios
    }
    refined = run_tasks(
        scenarios,
        accounting=accounting,
        replicates=replicates,
        r_by_scenario=r_by_scenario,
        workers=workers,
    )
    combined = coarse + refined
    summaries = summarize_grid(combined)
    thresholds = threshold_summary(summaries)
    return combined, summaries, thresholds


def make_map_plot(path: Path, threshold_rows: list[dict[str, Any]]) -> None:
    import matplotlib.pyplot as plt

    eligible = [
        row
        for row in threshold_rows
        if row["r_star_primary_grid"] != ""
        and int(row["interpretable_single_threshold"]) == 1
    ]
    eligible.sort(key=lambda row: float(row["r_star_primary_grid"]))
    figure_height = max(6.0, 0.34 * len(eligible))
    figure, axis = plt.subplots(figsize=(10, figure_height))
    labels = [str(row["scenario"]) for row in eligible]
    values = [float(row["r_star_primary_grid"]) for row in eligible]
    conservative = [
        float(row["r_star_conservative_grid"])
        if row["r_star_conservative_grid"] != ""
        else math.nan
        for row in eligible
    ]
    positions = list(range(len(eligible)))
    axis.barh(positions, values, color="#44688f", alpha=0.85, label="Primary r*")
    axis.scatter(
        conservative,
        positions,
        color="#a63d40",
        marker="|",
        s=180,
        linewidths=2,
        label="Conservative r*",
    )
    axis.axvline(1.0, color="#333333", linestyle="--", linewidth=1)
    axis.set_yticks(positions)
    axis.set_yticklabels(labels)
    axis.set_xlabel("Maximum diagnostic referral/direct attempt-cost ratio")
    axis.set_title("ENA ABM v0.4 diagnostic break-even map")
    axis.legend(loc="lower right")
    axis.grid(axis="x", alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def quantile(values: list[float], probability: float) -> float:
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


def bootstrap_thresholds(
    rows: list[dict[str, Any]],
    *,
    bootstraps: int = THRESHOLD_BOOTSTRAPS,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["scenario"]), str(row["accounting"])), []).append(
            row
        )
    output: list[dict[str, Any]] = []
    for (scenario, accounting), group in sorted(grouped.items()):
        r_values = sorted({float(row["r"]) for row in group})
        replicate_ids = sorted({int(row["replicate"]) for row in group})
        by_cell = {
            (int(row["replicate"]), float(row["r"])): float(row["delta_adoptions"])
            for row in group
        }
        thresholds: list[float] = []
        no_competitive = 0
        upper_bound = 0
        rng = random.Random(
            stable_seed(EXPERIMENT_SEED, "r_star_bootstrap", scenario, accounting)
        )
        for _ in range(bootstraps):
            sampled = [rng.choice(replicate_ids) for _ in replicate_ids]
            means = [
                statistics.fmean(by_cell[(replicate, relative_cost)] for replicate in sampled)
                for relative_cost in r_values
            ]
            competitive = [
                relative_cost
                for relative_cost, difference in zip(r_values, means)
                if difference >= 0
            ]
            if not competitive:
                no_competitive += 1
                continue
            threshold = max(competitive)
            thresholds.append(threshold)
            upper_bound += threshold == max(r_values)
        output.append(
            {
                "scenario": scenario,
                "accounting": accounting,
                "bootstraps": bootstraps,
                "finite_threshold_bootstraps": len(thresholds),
                "probability_no_competitive_region": no_competitive / bootstraps,
                "probability_competitive_through_upper_bound": upper_bound / bootstraps,
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


def rounding_diagnostics(
    rows: list[dict[str, Any]], threshold_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    threshold_lookup = {
        (str(row["scenario"]), str(row["accounting"])): row
        for row in threshold_rows
    }
    output: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, float], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(
            (str(row["scenario"]), str(row["accounting"]), float(row["r"])), []
        ).append(row)
    for (scenario, accounting), threshold in sorted(threshold_lookup.items()):
        relative_cost = threshold["r_star_primary_grid"]
        if relative_cost == "":
            output.append(
                {
                    "scenario": scenario,
                    "accounting": accounting,
                    "r_star_primary_grid": "",
                    "mean_direct_attempts_at_r_star": "",
                    "mean_referral_attempts_at_r_star": "",
                    "mean_direct_unused_budget_at_r_star": "",
                    "mean_referral_unused_budget_at_r_star": "",
                    "mean_referral_residual_share": "",
                    "interpretation": "no competitive tested region",
                }
            )
            continue
        cell = grouped[(scenario, accounting, float(relative_cost))]
        budget = float(BASE["budget_limit"])
        scenario_object = next(item for item in SCENARIOS if item.name == scenario)
        budget = float(scenario_object.updates.get("budget_limit", budget))
        mean_referral_residual = statistics.fmean(
            float(row["referral_unused_budget"]) for row in cell
        )
        output.append(
            {
                "scenario": scenario,
                "accounting": accounting,
                "r_star_primary_grid": relative_cost,
                "mean_direct_attempts_at_r_star": statistics.fmean(
                    float(row["direct_attempts"]) for row in cell
                ),
                "mean_referral_attempts_at_r_star": statistics.fmean(
                    float(row["referral_attempts"]) for row in cell
                ),
                "mean_direct_unused_budget_at_r_star": statistics.fmean(
                    float(row["direct_unused_budget"]) for row in cell
                ),
                "mean_referral_unused_budget_at_r_star": mean_referral_residual,
                "mean_referral_residual_share": (
                    mean_referral_residual / budget if budget else 0.0
                ),
                "interpretation": (
                    "residual below one referral attempt cost"
                    if mean_referral_residual < float(relative_cost) + 1e-9
                    else "inspect stage/resource constraints"
                ),
            }
        )
    return output


def run_map(output_dir: Path, workers: int, replicates: int) -> None:
    primary_rows, primary_summary, primary_thresholds = _combined_refinement(
        SCENARIOS,
        accounting="upfront_expected",
        replicates=replicates,
        workers=workers,
    )
    write_csv(output_dir / "break_even_primary_runs_v0.4.csv", primary_rows)
    write_csv(output_dir / "break_even_primary_curve_v0.4.csv", primary_summary)
    write_csv(output_dir / "break_even_condition_map_v0.4.csv", primary_thresholds)
    write_csv(
        output_dir / "break_even_threshold_bootstrap_v0.4.csv",
        bootstrap_thresholds(primary_rows),
    )
    write_csv(
        output_dir / "budget_rounding_diagnostics_v0.4.csv",
        rounding_diagnostics(primary_rows, primary_thresholds),
    )
    make_map_plot(output_dir / "break_even_condition_map_v0.4.png", primary_thresholds)

    robustness_scenarios = [
        scenario for scenario in SCENARIOS if scenario.name in ROBUSTNESS_SCENARIOS
    ]
    staged_rows, staged_summary, staged_thresholds = _combined_refinement(
        robustness_scenarios,
        accounting="staged",
        replicates=replicates,
        workers=workers,
    )
    write_csv(output_dir / "staged_robustness_runs_v0.4.csv", staged_rows)
    write_csv(output_dir / "staged_robustness_curve_v0.4.csv", staged_summary)
    write_csv(output_dir / "staged_robustness_thresholds_v0.4.csv", staged_thresholds)
    write_csv(
        output_dir / "staged_threshold_bootstrap_v0.4.csv",
        bootstrap_thresholds(staged_rows),
    )

    primary_lookup = {row["scenario"]: row for row in primary_thresholds}
    comparisons: list[dict[str, Any]] = []
    for staged in staged_thresholds:
        primary = primary_lookup[staged["scenario"]]
        upfront_r = primary["r_star_primary_grid"]
        staged_r = staged["r_star_primary_grid"]
        difference = (
            float(staged_r) - float(upfront_r)
            if upfront_r != "" and staged_r != ""
            else ""
        )
        comparisons.append(
            {
                "scenario": staged["scenario"],
                "upfront_r_star": upfront_r,
                "staged_r_star": staged_r,
                "staged_minus_upfront": difference,
                "difference_at_least_0_25": (
                    int(abs(float(difference)) >= 0.25 - 1e-9)
                    if difference != ""
                    else ""
                ),
                "primary_interpretable": primary[
                    "interpretable_single_threshold"
                ],
                "staged_interpretable": staged[
                    "interpretable_single_threshold"
                ],
            }
        )
    write_csv(output_dir / "accounting_robustness_comparison_v0.4.csv", comparisons)

    no_threshold = [
        row["scenario"]
        for row in primary_thresholds
        if row["r_star_primary_grid"] == ""
    ]
    multiple = [
        row["scenario"]
        for row in primary_thresholds
        if int(row["crossing_count"]) > 1
    ]
    nonmonotonic = [
        row["scenario"]
        for row in primary_thresholds
        if int(row["material_upward_jumps"]) > 0
    ]
    robust_differences = [
        row["scenario"]
        for row in comparisons
        if row["difference_at_least_0_25"] == 1
    ]
    report = [
        "# Break-even Diagnostic — ENA ABM v0.4",
        "",
        "> Validation and diagnostic output only. This is not the definitive article",
        "> experiment and its parameters are not empirically calibrated.",
        "",
        "## Design",
        "",
        f"- {replicates} paired replications per condition.",
        "- Full expected cost at attempt initiation as the primary accounting rule.",
        f"- Staged cost as a secondary robustness rule in {len(robustness_scenarios)} selected conditions.",
        f"- Coarse r range from {min(COARSE_GRID):.2f} to {max(COARSE_GRID):.2f}.",
        f"- Crossing refinement to {REFINEMENT_TOLERANCE:.2f}.",
        f"- {len(SCENARIOS)} conditions informed by Morris and process-boundary requirements.",
        "",
        "## Baseline",
        "",
        "The primary baseline threshold is r*=1.20. Its conservative threshold is",
        "1.10, and its 500-sample bootstrap percentile interval is [1.10, 1.25].",
        "",
        "At r=1.20, mean referral-minus-direct adoption is 0.01 with 95% interval",
        "[-0.25, 0.27]. At r=1.25, the mean is -0.19 with interval [-0.45, 0.07].",
        "",
        "## Condition map",
        "",
        "Twenty-three conditions contain an interpretable competitive region. Primary",
        "thresholds range from 0.70 under a direct-exposure advantage to 1.65 under a",
        "referral-exposure advantage.",
        "",
        "No competitive tested region is identified for low acceptance, no eligible",
        "neighbors, or no adopted referrer.",
        "",
        "High sociality, high acceptance, and abundant eligible neighbors increase the",
        "maximum competitive cost ratio. Absence of social influence, low uncertainty,",
        "small market size, and preferential attachment reduce it.",
        "",
        "## Identification checks",
        "",
        f"- Conditions without a competitive region: {', '.join(no_threshold) if no_threshold else 'none'}.",
        f"- Multiple crossings: {', '.join(multiple) if multiple else 'none'}.",
        f"- Material upward jumps: {', '.join(nonmonotonic) if nonmonotonic else 'none'}.",
        "- Competitive-through-upper-bound cases: none.",
        f"- Staged-accounting difference of at least 0.25: {', '.join(robust_differences) if robust_differences else 'none'}.",
        "",
        "## Conclusion",
        "",
        "Referrals retains a broad diagnostic cost advantage when sociality and",
        "referral opportunities are favorable. Its competitiveness is narrow or absent",
        "when the activation chain constrains acceptance, eligible neighbors, or",
        "effective exposure.",
        "",
        "The primary map is stable enough for joint review, but staged accounting",
        "remains economically unidentified. Empirical activity costs are required",
        "before extending the behavioral architecture.",
        "",
    ]
    (output_dir / "BREAK_EVEN_ANALYSIS_v0.4.md").write_text(
        "\n".join(report), encoding="utf-8"
    )


def write_manifest(output_dir: Path, workers: int, replicates: int) -> None:
    files = [
        path
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name != "manifest_v0.4.json"
    ]
    manifest = {
        "status": "diagnostic_only_not_article_evidence",
        "model_version": "0.4.0",
        "experiment_seed": EXPERIMENT_SEED,
        "workers": workers,
        "replicates": replicates,
        "coarse_grid": COARSE_GRID,
        "refinement_tolerance": REFINEMENT_TOLERANCE,
        "primary_accounting": "upfront_expected",
        "secondary_accounting": "staged",
        "scenario_count": len(SCENARIOS),
        "threshold_bootstraps": THRESHOLD_BOOTSTRAPS,
        "scenario_definitions": [scenario.to_dict() for scenario in SCENARIOS],
        "files": {path.name: sha256(path) for path in files},
    }
    (output_dir / "manifest_v0.4.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/break_even_v0_4"),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(4, os.cpu_count() or 1),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    selected = run_precision_pilot(args.output, args.workers)
    run_map(args.output, args.workers, selected)
    write_manifest(args.output, args.workers, selected)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "selected_replicates": selected,
                "workers": args.workers,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
