"""Rewrite v0.5 gzip outputs with deterministic headers (mtime=0)."""

from __future__ import annotations

import argparse
import gzip
import io
from pathlib import Path


def canonicalize(path: Path) -> None:
    with gzip.open(path, "rb") as source:
        data = source.read()
    temporary = path.with_suffix(path.suffix + ".canonical")
    with temporary.open("wb") as binary:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=binary, mtime=0
        ) as target:
            target.write(data)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directories", nargs="+", type=Path)
    args = parser.parse_args()
    count = 0
    for directory in args.directories:
        for path in sorted(directory.glob("*.csv.gz")):
            canonicalize(path)
            count += 1
    print(f"Canonicalized {count} gzip files.")


if __name__ == "__main__":
    main()
