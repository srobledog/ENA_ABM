"""Verify that the v0.4 model source copied into v0.5 is unchanged."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs" / "final_hashes_v0.4.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    expected: dict[str, str] = {}
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["file"].startswith("src/ena_abm/"):
                expected[row["file"]] = row["sha256"]
    if not expected:
        raise SystemExit("No v0.4 source hashes were found.")
    failures: list[str] = []
    for relative, digest in sorted(expected.items()):
        path = ROOT / relative
        observed = sha256(path) if path.exists() else "MISSING"
        if observed != digest:
            failures.append(f"{relative}: expected {digest}, observed {observed}")
    if failures:
        raise SystemExit("Frozen v0.4 source mismatch:\n" + "\n".join(failures))
    print(f"PASS: {len(expected)} frozen v0.4 model-source files match.")


if __name__ == "__main__":
    main()
