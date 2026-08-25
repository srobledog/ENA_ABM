from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    first_files = {
        path.relative_to(arguments.first): path
        for path in arguments.first.rglob("*")
        if path.is_file() and "visualizations" not in path.parts
    }
    second_files = {
        path.relative_to(arguments.second): path
        for path in arguments.second.rglob("*")
        if path.is_file() and "visualizations" not in path.parts
    }
    if first_files.keys() != second_files.keys():
        raise SystemExit("run directories contain different primary file sets")

    rows = []
    for relative in sorted(first_files):
        first_hash = digest(first_files[relative])
        second_hash = digest(second_files[relative])
        rows.append(
            {
                "relative_path": str(relative),
                "run1_sha256": first_hash,
                "run2_sha256": second_hash,
                "identical": int(first_hash == second_hash),
            }
        )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if not all(row["identical"] for row in rows):
        raise SystemExit("one or more primary files differ")
    print(f"Verified {len(rows)} byte-identical primary files")


if __name__ == "__main__":
    main()
