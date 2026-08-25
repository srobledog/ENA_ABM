"""Check the minimum acceptance criteria for two complete v0.5 runs."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run1", type=Path)
    parser.add_argument("run2", type=Path)
    parser.add_argument("comparison", type=Path)
    args = parser.parse_args()
    for run in (args.run1, args.run2):
        manifest = json.loads((run / "manifest_v0.5.json").read_text(encoding="utf-8"))
        assert manifest["total_paired_rows"] == 972800, (run, "paired rows")
        assert manifest["principal_files"] == 34, (run, "principal files")
        assert manifest["interpretation_blocked"] is False, (run, "stop gate")
        assert manifest["parameters_empirically_calibrated"] is False
    with args.comparison.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 34, "comparison must contain 34 principal files"
    assert all(row["identical"] == "1" for row in rows), "logical mismatch"
    assert all(row["binary_identical"] == "1" for row in rows), "byte mismatch"
    print("PASS: expected v0.5 row counts, manifests, stop gate, and 34-file identity confirmed.")

if __name__ == "__main__":
    main()
