from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


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


def summarize_runs(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (str(row["network_type"]), float(row["market_sociality"]), str(row["strategy"]))
        ].append(row)
    summaries: list[dict[str, Any]] = []
    for (network_type, sociality, strategy), group in sorted(groups.items()):
        adoptions = [float(row["new_adoptions"]) for row in group]
        summaries.append(
            {
                "network_type": network_type,
                "market_sociality": sociality,
                "strategy": strategy,
                "replicates": len(group),
                "mean_new_adoptions": statistics.fmean(adoptions),
                "sd_new_adoptions": statistics.stdev(adoptions)
                if len(adoptions) > 1
                else 0.0,
                "median_new_adoptions": statistics.median(adoptions),
                "p10_new_adoptions": _quantile(adoptions, 0.10),
                "p90_new_adoptions": _quantile(adoptions, 0.90),
                "takeoff_rate": statistics.fmean(float(row["takeoff"]) for row in group),
                "extinction_rate": statistics.fmean(
                    float(row["extinction"]) for row in group
                ),
                "mean_action_utilization": statistics.fmean(
                    float(row["action_utilization"]) for row in group
                ),
                "mean_awareness_rate": statistics.fmean(
                    float(row["awareness_rate_nonseed"]) for row in group
                ),
            }
        )
    return summaries


def paired_differences(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: dict[tuple[str, float, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = (
            str(row["network_type"]),
            float(row["market_sociality"]),
            int(row["replicate_id"]),
        )
        pairs[key][str(row["strategy"])] = row
    grouped: dict[tuple[str, float], list[float]] = defaultdict(list)
    for (network_type, sociality, _), strategies in pairs.items():
        if {"direct", "referral"} <= strategies.keys():
            grouped[(network_type, sociality)].append(
                float(strategies["referral"]["new_adoptions"])
                - float(strategies["direct"]["new_adoptions"])
            )
    output: list[dict[str, Any]] = []
    for (network_type, sociality), differences in sorted(grouped.items()):
        output.append(
            {
                "network_type": network_type,
                "market_sociality": sociality,
                "paired_replicates": len(differences),
                "mean_referral_minus_direct": statistics.fmean(differences),
                "median_referral_minus_direct": statistics.median(differences),
                "share_referral_higher": statistics.fmean(
                    difference > 0 for difference in differences
                ),
                "share_equal": statistics.fmean(
                    difference == 0 for difference in differences
                ),
            }
        )
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_pilot_report(
    path: Path,
    run_count: int,
    summaries: list[dict[str, Any]],
    paired: list[dict[str, Any]],
) -> None:
    lines = [
        "# Pilot diagnostics — ENA ABM v0.3",
        "",
        f"Runs completed: {run_count}.",
        "",
        "> These are software-verification and exploratory pilot diagnostics. "
        "They are not findings for the article and the parameters are not calibrated.",
        "",
        "## Cell summaries",
        "",
        "| Network | Sociality | Strategy | Mean new adoptions | SD | Takeoff rate | Action utilization |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            "| {network_type} | {market_sociality:.2f} | {strategy} | "
            "{mean_new_adoptions:.2f} | {sd_new_adoptions:.2f} | "
            "{takeoff_rate:.2f} | {mean_action_utilization:.2f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Paired strategy diagnostics",
            "",
            "| Network | Sociality | Mean referral − direct | Referral higher | Equal |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in paired:
        lines.append(
            "| {network_type} | {market_sociality:.2f} | "
            "{mean_referral_minus_direct:.2f} | {share_referral_higher:.2f} | "
            "{share_equal:.2f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The tables confirm that the implementation responds to the experimental factors "
            "and that paired scenarios can be reproduced. They do not establish theoretical "
            "effects, empirical thresholds, managerial recommendations, or article conclusions.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
