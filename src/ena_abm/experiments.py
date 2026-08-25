from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path
from typing import Any

from .analysis import paired_differences, summarize_runs, write_csv, write_pilot_report
from .config import ModelConfig
from .model import EntrepreneurialNetworkActivationModel
from .rng import stable_seed


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("experiment produced no rows")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_pilot(config_path: Path, output_dir: Path) -> dict[str, Path | int]:
    specification = json.loads(config_path.read_text(encoding="utf-8"))
    base_config = dict(specification["base_config"])
    factors = specification["factors"]
    replicates = int(specification["replicates"])
    experiment_seed = int(specification["experiment_seed"])

    summaries: list[dict[str, Any]] = []
    ticks: list[dict[str, Any]] = []
    for network_type, sociality, replicate_id in itertools.product(
        factors["network_type"],
        factors["market_sociality"],
        range(replicates),
    ):
        paired_master_seed = stable_seed(
            experiment_seed, network_type, sociality, replicate_id
        )
        pair_signature: str | None = None
        for strategy in factors["strategy"]:
            values = {
                **base_config,
                "network_type": network_type,
                "market_sociality": sociality,
                "strategy": strategy,
                "master_seed": paired_master_seed,
                "replicate_id": replicate_id,
            }
            config = ModelConfig.from_dict(values)
            output = EntrepreneurialNetworkActivationModel(config).run()
            if pair_signature is None:
                pair_signature = output.initialization_signature
            elif pair_signature != output.initialization_signature:
                raise AssertionError("paired strategies do not share initialization")
            summaries.append(output.summary)
            ticks.extend(
                {
                    "scenario_id": output.summary["scenario_id"],
                    "replicate_id": replicate_id,
                    "strategy": strategy,
                    "network_type": network_type,
                    "market_sociality": sociality,
                    **record,
                }
                for record in output.ticks
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    runs_path = output_dir / "pilot_runs.csv"
    ticks_path = output_dir / "pilot_ticks.csv"
    summary_path = output_dir / "pilot_summary.csv"
    paired_path = output_dir / "pilot_paired_differences.csv"
    report_path = output_dir / "pilot_report.md"
    manifest_path = output_dir / "pilot_manifest.json"

    _write_rows(runs_path, summaries)
    _write_rows(ticks_path, ticks)
    cell_summaries = summarize_runs(summaries)
    paired = paired_differences(summaries)
    write_csv(summary_path, cell_summaries)
    write_csv(paired_path, paired)
    write_pilot_report(report_path, len(summaries), cell_summaries, paired)
    manifest_path.write_text(
        json.dumps(
            {
                "model_version": "0.3.0",
                "specification_version": "0.3",
                "experiment_seed": experiment_seed,
                "run_count": len(summaries),
                "cell_count": len(cell_summaries),
                "paired_cell_count": len(paired),
                "configuration": specification,
                "interpretation_status": "verification_and_exploratory_pilot_only",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "run_count": len(summaries),
        "runs": runs_path,
        "ticks": ticks_path,
        "summary": summary_path,
        "paired": paired_path,
        "report": report_path,
        "manifest": manifest_path,
    }
