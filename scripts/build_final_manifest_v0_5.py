"""Build the final v0.5 package manifest."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "final_hashes_v0.5.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    text = str(relative)
    if "__pycache__" in relative.parts or path.suffix == ".pyc":
        return False
    if text.startswith("outputs/main_study_v0_5/run2/"):
        return path.name in {"manifest_v0.5.json", "principal_hashes_v0.5.csv"}
    if text.startswith("outputs/break_even_v0_4/"):
        return False
    if text.startswith("outputs/costing_template_v0_4/"):
        return False
    if text.startswith("outputs/process_registry_v0_4/"):
        return False
    if text.startswith("outputs/validation_v0_4/"):
        return False
    if text in {
        "outputs/reproduction_hashes_v0.4.csv",
        "outputs/test_results_v0.4.txt",
    }:
        return False
    return True


def main() -> None:
    files = [
        path
        for path in sorted(ROOT.rglob("*"))
        if path.is_file() and included(path) and path != OUTPUT
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["sha256", "bytes", "file"]
        )
        writer.writeheader()
        for path in files:
            writer.writerow(
                {
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                    "file": str(path.relative_to(ROOT)),
                }
            )
    print(f"Wrote {len(files)} hashes to {OUTPUT}.")


if __name__ == "__main__":
    main()
