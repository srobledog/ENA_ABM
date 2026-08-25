"""Write SHA-256 manifest for the final v0.4 package contents."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(".")
OUTPUT = Path("outputs/final_hashes_v0.4.csv")


def excluded(path: Path) -> bool:
    text = path.as_posix()
    return (
        not path.is_file()
        or "outputs/reproduction_2/" in text
        or "/__pycache__/" in f"/{text}"
        or path.suffix == ".pyc"
        or (
            "outputs/costing_template_v0_4/" in text
            and path.suffix in {".png", ".ndjson"}
        )
        or path == OUTPUT
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    rows = [
        {"sha256": sha256(path), "file": path.as_posix()}
        for path in sorted(ROOT.rglob("*"))
        if not excluded(path)
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sha256", "file"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"hashed {len(rows)} files")


if __name__ == "__main__":
    main()
