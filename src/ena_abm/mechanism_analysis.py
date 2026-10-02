"""Confirmatory block bootstrap for the ENA ABM mechanism experiment."""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import platform
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np

from .rng import stable_seed

ROOT = Path(__file__).resolve().parents[2]
METRICS = tuple(
    (r, schedule, contrast)
    for r in (1.0, 1.2)
    for schedule in ("N", "E")
    for contrast in ("G", "L", "B", "I")
) + tuple(
    (r, "N-E", contrast)
    for r in (1.0, 1.2)
    for contrast in ("Q_L1", "Q_A1", "Q_L0", "Q_A0")
)
PRIMARY = frozenset((r, "N", contrast) for r in (1.0, 1.2) for contrast in ("G", "L", "B", "I"))
GAP_FIELDS = {"L1": "G", "A1": "G_A1", "L0": "G_L0", "A0": "G_A0"}


def _read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path, rows, fieldnames=None):
    rows = list(rows)
    if fieldnames is None:
        fieldnames = list(rows[0])
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_gzip_csv(path, expected_rows):
    """Read through EOF to validate gzip CRC and report logical content metadata."""
    digest = hashlib.sha256()
    uncompressed_bytes = 0
    with gzip.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            uncompressed_bytes += len(chunk)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = sum(1 for _ in reader)
    if rows != expected_rows:
        raise ValueError(f"gzip CSV row count is {rows}; expected {expected_rows}")
    return {
        "rows": rows,
        "sha256": _sha256(path),
        "content_sha256": digest.hexdigest(),
        "uncompressed_bytes": uncompressed_bytes,
    }


def _write_gzip_csv_atomic(path, fieldnames, rows, expected_rows):
    """Publish a gzip CSV only after its stream is closed and durable."""
    path = Path(path)
    temporary = path.with_name(path.name + ".part")
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(filename="", fileobj=raw, mode="wb", compresslevel=6, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temporary, path)
        return _verify_gzip_csv(path, expected_rows)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _fmt(value):
    if value is None or value == "":
        return ""
    return format(float(value), ".17g")


def _sociality_band(value):
    if 0 <= value < 1 / 3:
        return "low_[0,1/3)"
    if 1 / 3 <= value < 2 / 3:
        return "intermediate_[1/3,2/3)"
    if 2 / 3 <= value <= 1:
        return "high_[2/3,1]"
    raise ValueError(f"market_sociality outside [0,1]: {value}")


def _classification(low, high, margin):
    if low > margin:
        return "positive_diagnostic"
    if high < -margin:
        return "negative_diagnostic"
    if low >= -margin and high <= margin:
        return "equivalent_within_margin"
    if low > 0 or high < 0:
        return "sign_supported_relevance_uncertain"
    return "inconclusive"


def _quantiles(values, adjusted=False):
    alpha = .05 / 8 if adjusted else .05
    low, high = np.quantile(values, [alpha / 2, 1 - alpha / 2], method="linear")
    return float(low), float(high)


def _validate_and_matrix(rows, expected_profiles, expected_replicates):
    """Return profile x replicate x metric counts after strict block validation."""
    cells = {}
    profile_replicates = defaultdict(set)
    block_cells = defaultdict(set)
    expected_cells = {(r, s) for r in (1.0, 1.2) for s in ("N", "E")}
    for row in rows:
        profile = row["profile_id"]
        replicate = int(row["replicate_id"])
        cost = float(row["r"])
        schedule = row["schedule"]
        key = (profile, replicate, cost, schedule)
        if key in cells:
            raise ValueError(f"duplicate contrast cell: {key}")
        if cost not in (1.0, 1.2) or schedule not in ("N", "E"):
            raise ValueError(f"unexpected contrast cell: {key}")
        cells[key] = {name: float(row[field]) for name, field in GAP_FIELDS.items()}
        profile_replicates[profile].add(replicate)
        block_cells[(profile, replicate)].add((cost, schedule))
    profiles = sorted(profile_replicates)
    if set(profiles) != set(expected_profiles):
        raise ValueError("profile set does not match the frozen stage")
    vectors = np.empty((len(profiles), expected_replicates, len(METRICS)), dtype=np.float64)
    for pidx, profile in enumerate(profiles):
        if profile_replicates[profile] != set(range(expected_replicates)):
            raise ValueError(f"replicates for {profile} are incomplete or nonconsecutive")
        for replicate in range(expected_replicates):
            if block_cells[(profile, replicate)] != expected_cells:
                raise ValueError(f"paired block is incomplete: {(profile, replicate)}")
            values = {}
            for cost, schedule in expected_cells:
                gap = cells[(profile, replicate, cost, schedule)]
                values[(cost, schedule, "G")] = gap["L1"]
                values[(cost, schedule, "L")] = gap["L1"] - gap["A1"]
                values[(cost, schedule, "B")] = gap["L1"] - gap["L0"]
                values[(cost, schedule, "I")] = gap["L1"] - gap["A1"] - gap["L0"] + gap["A0"]
            for cost in (1.0, 1.2):
                for arm in GAP_FIELDS:
                    values[(cost, "N-E", "Q_" + arm)] = (
                        cells[(profile, replicate, cost, "N")][arm]
                        - cells[(profile, replicate, cost, "E")][arm]
                    )
            vectors[pidx, replicate] = [values[metric] for metric in METRICS]
    return profiles, vectors


def _bootstrap(vectors, profiles, samples, seed, chunk_size=1000):
    """Resample complete replicate blocks independently within each profile."""
    n_profiles, replicates, n_metrics = vectors.shape
    boot = np.empty((n_profiles, samples, n_metrics), dtype=np.float64)
    for pidx, profile in enumerate(profiles):
        rng = np.random.Generator(np.random.PCG64(stable_seed(seed, "profile_bootstrap", profile)))
        for start in range(0, samples, chunk_size):
            stop = min(samples, start + chunk_size)
            indices = rng.integers(0, replicates, size=(stop - start, replicates), dtype=np.int32)
            boot[pidx, start:stop] = vectors[pidx][indices].mean(axis=1)
    return boot


def _estimate_rows(profiles, point, boot, profile_metadata, margin):
    profile_rows = []
    for pidx, profile in enumerate(profiles):
        meta = profile_metadata[profile]
        for midx, (cost, schedule, contrast) in enumerate(METRICS):
            low, high = _quantiles(boot[pidx, :, midx])
            for scale, factor in (("new_adopters", 1.0), ("percentage_points_of_available", meta["percentage_factor"])):
                profile_rows.append({
                    "profile_id": profile, "network_type": meta["network_type"],
                    "market_sociality": _fmt(meta["market_sociality"]), "budget_limit": _fmt(meta["budget_limit"]),
                    "seed_adopters": meta["seed_adopters"], "relative_cost": _fmt(cost), "schedule": schedule,
                    "contrast": contrast, "family": "primary" if (cost, schedule, contrast) in PRIMARY else "secondary",
                    "scale": scale, "estimate": _fmt(point[pidx, midx] * factor),
                    "ci95_low": _fmt(low * factor), "ci95_high": _fmt(high * factor),
                })
    design_rows = []
    for midx, (cost, schedule, contrast) in enumerate(METRICS):
        primary = (cost, schedule, contrast) in PRIMARY
        for scale in ("new_adopters", "percentage_points_of_available"):
            confirmatory = primary and scale == "new_adopters"
            factors = np.ones(len(profiles)) if scale == "new_adopters" else np.array(
                [profile_metadata[p]["percentage_factor"] for p in profiles]
            )
            estimate = float(np.mean(point[:, midx] * factors))
            distribution = np.mean(boot[:, :, midx] * factors[:, None], axis=0)
            low95, high95 = _quantiles(distribution)
            lowadj, highadj = _quantiles(distribution, adjusted=True) if confirmatory else (None, None)
            row = {
                "relative_cost": _fmt(cost), "schedule": schedule, "contrast": contrast,
                "family": "primary" if primary else "secondary", "scale": scale,
                "estimate": _fmt(estimate), "ci95_low": _fmt(low95), "ci95_high": _fmt(high95),
                "ci99_375_bonferroni_low": _fmt(lowadj), "ci99_375_bonferroni_high": _fmt(highadj),
                "diagnostic_margin": _fmt(margin if confirmatory else None),
                "interpretation": _classification(lowadj, highadj, margin) if confirmatory else "descriptive",
            }
            design_rows.append(row)
    return profile_rows, design_rows


def _subgroup_rows(profiles, point, boot, metadata):
    dimensions = {
        "network_type": lambda m: m["network_type"],
        "sociality_band": lambda m: _sociality_band(m["market_sociality"]),
        "budget_limit": lambda m: _fmt(m["budget_limit"]),
        "seed_adopters": lambda m: str(m["seed_adopters"]),
    }
    rows = []
    for dimension, getter in dimensions.items():
        groups = defaultdict(list)
        for pidx, profile in enumerate(profiles):
            groups[getter(metadata[profile])].append(pidx)
        for group in sorted(groups):
            indices = groups[group]
            for midx, (cost, schedule, contrast) in enumerate(METRICS):
                for scale in ("new_adopters", "percentage_points_of_available"):
                    factors = np.ones(len(indices)) if scale == "new_adopters" else np.array(
                        [metadata[profiles[i]]["percentage_factor"] for i in indices]
                    )
                    estimate = float(np.mean(point[indices, midx] * factors))
                    distribution = np.mean(boot[indices, :, midx] * factors[:, None], axis=0)
                    low, high = _quantiles(distribution)
                    rows.append({"group_dimension": dimension, "group": group, "profiles": len(indices),
                        "relative_cost": _fmt(cost), "schedule": schedule, "contrast": contrast,
                        "family": "primary" if (cost, schedule, contrast) in PRIMARY else "secondary",
                        "scale": scale, "estimate": _fmt(estimate), "ci95_low": _fmt(low), "ci95_high": _fmt(high)})
    return rows


def analyze(input_dir, output_dir, specification_path, *, allow_technical_pilot=False, bootstrap_samples=None):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    specification = json.loads(Path(specification_path).read_text())
    manifest = json.loads((input_dir / "manifest.json").read_text())
    stage = manifest["stage"]
    if stage != "main" and not allow_technical_pilot:
        raise ValueError("confirmatory reporting requires a main-stage dataset")
    if manifest.get("specification") != specification:
        raise ValueError("execution manifest and analysis specification differ")
    expected_profiles = [row["profile"] for row in _read_csv(input_dir / "profiles.csv")]
    registered_profiles = [row["profile"] for row in _read_csv(ROOT / "results/summaries/registered_profiles_v0.5.csv")]
    frozen_profiles = registered_profiles if stage == "main" else specification["pilot_profiles"]
    if expected_profiles != frozen_profiles:
        raise ValueError("stage profiles do not match the frozen profile registry")
    expected_replicates = specification["main_replicates"] if stage == "main" else specification["pilot_replicates"]
    if manifest["profiles"] != len(expected_profiles) or manifest["replicates"] != expected_replicates:
        raise ValueError("manifest does not match the configured stage")
    paired_path = input_dir / "paired_contrasts.csv"
    recorded_hash = manifest.get("full_data_sha256", {}).get("paired_contrasts.csv")
    if recorded_hash and _sha256(paired_path) != recorded_hash:
        raise ValueError("paired contrasts do not match the execution manifest")
    profiles, vectors = _validate_and_matrix(_read_csv(paired_path), expected_profiles, expected_replicates)
    profile_rows = {row["profile"]: row for row in _read_csv(input_dir / "profiles.csv")}
    metadata = {}
    for profile in profiles:
        row = profile_rows[profile]
        seeds = int(float(row["seed_adopters"]))
        metadata[profile] = {"network_type": row["network_type"], "market_sociality": float(row["market_sociality"]),
            "budget_limit": float(row["budget_limit"]), "seed_adopters": seeds, "percentage_factor": 100 / (100 - seeds)}
    samples = int(specification["bootstrap_samples"] if bootstrap_samples is None else bootstrap_samples)
    if stage == "main" and samples != int(specification["bootstrap_samples"]):
        raise ValueError("main-stage bootstrap sample count is frozen by the protocol")
    if samples < 2:
        raise ValueError("bootstrap_samples must be at least 2")
    point = vectors.mean(axis=1)
    boot = _bootstrap(vectors, profiles, samples, int(specification["resampling_seed"]))
    output_dir.mkdir(parents=True, exist_ok=False)
    profile_estimates, design_estimates = _estimate_rows(profiles, point, boot, metadata, float(specification["diagnostic_margin"]))
    subgroup_estimates = _subgroup_rows(profiles, point, boot, metadata)
    _write_csv(output_dir / "profile_estimates.csv", profile_estimates)
    _write_csv(output_dir / "design_estimates.csv", design_estimates)
    _write_csv(output_dir / "subgroup_estimates.csv", subgroup_estimates)
    bootstrap_path = output_dir / "bootstrap_design_means.csv.gz"
    fieldnames = ["bootstrap_sample"] + [
        f"{c}_{s}_{k}_{scale}" for c, s, k in METRICS for scale in ("count", "pp")
    ]
    factors = np.array([metadata[p]["percentage_factor"] for p in profiles])[:, None]
    design_count = boot.mean(axis=0)
    design_pp = (boot * factors[:, None, :]).mean(axis=0)

    def bootstrap_rows():
        for sample in range(samples):
            row = {"bootstrap_sample": sample}
            for midx, metric in enumerate(METRICS):
                prefix = f"{metric[0]}_{metric[1]}_{metric[2]}"
                row[prefix + "_count"] = _fmt(design_count[sample, midx])
                row[prefix + "_pp"] = _fmt(design_pp[sample, midx])
            yield row

    bootstrap_file = _write_gzip_csv_atomic(
        bootstrap_path, fieldnames, bootstrap_rows(), expected_rows=samples
    )
    analysis_manifest = {
        "protocol_version": specification["protocol_version"], "stage": stage,
        "status": "technical_pilot_analysis_only" if stage != "main" else "confirmatory",
        "input_manifest_sha256": _sha256(input_dir / "manifest.json"),
        "paired_contrasts_sha256": _sha256(paired_path), "profiles": len(profiles),
        "replicates_per_profile": expected_replicates, "bootstrap_samples": samples,
        "resampling_seed": specification["resampling_seed"], "generator": "numpy.PCG64",
        "block_unit": "replicate with all arms, costs, and schedules within profile",
        "profile_weighting": "equal", "profile_resampling": False,
        "quantile_method": "linear", "nominal_interval": .95,
        "primary_family_size": 8, "primary_bonferroni_interval": .99375,
        "diagnostic_margin_new_adopters": specification["diagnostic_margin"],
        "bootstrap_file": bootstrap_file,
        "numpy": np.__version__, "python": platform.python_version(),
        "analysis_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2], text=True).strip(),
    }
    analysis_manifest["output_sha256"] = {p.name: _sha256(p) for p in sorted(output_dir.iterdir()) if p.is_file()}
    (output_dir / "analysis_manifest.json").write_text(json.dumps(analysis_manifest, indent=2, sort_keys=True) + "\n")
    return analysis_manifest
