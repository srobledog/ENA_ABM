from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def morris_plot(input_dir: Path, output_dir: Path) -> None:
    rows = _read(input_dir / "morris" / "morris_indices_v0.3.csv")
    outcomes = [
        ("paired_adoption_difference", "Referral − direct adoptions"),
        ("mean_adoptions", "Mean adoptions"),
    ]
    figure, axes = plt.subplots(1, 2, figsize=(13, 7), constrained_layout=True)
    for axis, (outcome, title) in zip(axes, outcomes):
        selected = [row for row in rows if row["outcome"] == outcome]
        selected.sort(key=lambda row: float(row["mu_star"]))
        names = [row["parameter"].replace("_", " ") for row in selected]
        mu_star = [float(row["mu_star"]) for row in selected]
        sigma = [float(row["sigma"]) for row in selected]
        axis.barh(names, mu_star, color="#356A8A")
        axis.scatter(mu_star, names, s=24, color="#173F5F", label="μ*")
        axis.set_title(title)
        axis.set_xlabel("Morris μ* (absolute elementary effect)")
        for y, value, interaction in zip(names, mu_star, sigma):
            axis.text(value, y, f"  σ={interaction:.1f}", va="center", fontsize=8)
        axis.grid(axis="x", alpha=0.2)
    figure.suptitle(
        "Morris screening — diagnostic only, not article evidence", fontsize=14
    )
    figure.savefig(output_dir / "morris_screening_v0.3.png", dpi=180)
    plt.close(figure)


def diagnostic_plot(input_dir: Path, output_dir: Path) -> None:
    rows = _read(
        input_dir / "diagnostics" / "diagnostic_paired_summary_v0.3.csv"
    )
    rows.sort(key=lambda row: float(row["mean_absolute_difference"]))
    labels = [row["scenario"].replace("_", " ") for row in rows]
    means = [float(row["mean_absolute_difference"]) for row in rows]
    standard_deviations = [float(row["sd_absolute_difference"]) for row in rows]
    colors = ["#B4473E" if value < 0 else "#3C8D5A" for value in means]
    figure, axis = plt.subplots(figsize=(11, 9), constrained_layout=True)
    axis.barh(labels, means, xerr=standard_deviations, color=colors, alpha=0.9)
    axis.axvline(0, color="#222222", linewidth=1)
    axis.set_xlabel("Mean referral − direct adoptions (error bars: between-run SD)")
    axis.set_title(
        "Diagnostic strategy contrasts — 50 paired replicates per scenario"
    )
    axis.grid(axis="x", alpha=0.2)
    figure.savefig(output_dir / "diagnostic_strategy_contrasts_v0.3.png", dpi=180)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    morris_plot(arguments.input_dir, arguments.output_dir)
    diagnostic_plot(arguments.input_dir, arguments.output_dir)


if __name__ == "__main__":
    main()
