"""Compare deterministic principal outputs from two v0.4 reproductions."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


FIRST = Path("outputs/break_even_v0_4")
SECOND = Path("outputs/reproduction_2/break_even_v0_4")
OUTPUT = Path("outputs/reproduction_hashes_v0.4.csv")
EXCLUDE = {"manifest_v0.4.json", "BREAK_EVEN_ANALYSIS_v0.4.md"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    rows = []
    for first in sorted(FIRST.iterdir()):
        if not first.is_file() or first.name in EXCLUDE:
            continue
        second = SECOND / first.name
        first_hash = sha256(first)
        second_hash = sha256(second) if second.exists() else ""
        rows.append(
            {
                "file": first.name,
                "first_sha256": first_hash,
                "second_sha256": second_hash,
                "match": int(first_hash == second_hash),
            }
        )
    if not rows or not all(row["match"] for row in rows):
        raise AssertionError("principal reproduction hashes do not all match")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} principal files match")


if __name__ == "__main__":
    main()
