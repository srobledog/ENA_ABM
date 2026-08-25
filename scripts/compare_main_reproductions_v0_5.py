"""Compare the principal output hashes of two independent v0.5 runs."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
from pathlib import Path


def read_manifest(path: Path) -> dict[str, str]:
    with (path / "principal_hashes_v0.5.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        return {row["file"]: row["sha256"] for row in csv.DictReader(handle)}


def logical_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run1", type=Path)
    parser.add_argument("run2", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/main_study_v0_5/reproduction_comparison_v0.5.csv"),
    )
    args = parser.parse_args()
    first = read_manifest(args.run1)
    second = read_manifest(args.run2)
    files = sorted(set(first) | set(second))
    rows = [
        {
            "file": name,
            "run1_sha256": first.get(name, ""),
            "run2_sha256": second.get(name, ""),
            "run1_logical_sha256": (
                logical_sha256(args.run1 / name) if name in first else ""
            ),
            "run2_logical_sha256": (
                logical_sha256(args.run2 / name) if name in second else ""
            ),
            "binary_identical": int(
                first.get(name) == second.get(name)
                and name in first
                and name in second
            ),
            "identical": int(
                name in first
                and name in second
                and logical_sha256(args.run1 / name)
                == logical_sha256(args.run2 / name)
            ),
        }
        for name in files
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    failures = [row["file"] for row in rows if not row["identical"]]
    if failures:
        raise SystemExit(
            f"FAIL: {len(failures)} principal outputs differ: {failures}"
        )
    print(f"PASS: {len(rows)} principal v0.5 outputs are byte-identical.")


if __name__ == "__main__":
    main()
