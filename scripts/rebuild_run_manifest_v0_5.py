"""Rebuild a v0.5 run manifest after deterministic gzip normalization."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    manifest_path = args.run_dir / "manifest_v0.5.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    principal = [
        path for path in sorted(args.run_dir.iterdir())
        if path.is_file()
        and path.name not in {"manifest_v0.5.json", "principal_hashes_v0.5.csv"}
        and path.suffix in {".csv", ".gz", ".json", ".md", ".png"}
    ]
    rows = [{"file": p.name, "sha256": sha256(p), "bytes": p.stat().st_size}
            for p in principal]
    with (args.run_dir / "principal_hashes_v0.5.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "sha256", "bytes"])
        writer.writeheader(); writer.writerows(rows)
    manifest["config_sha256"] = sha256(args.config)
    manifest["principal_files"] = len(rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    print(f"Rebuilt {len(rows)} principal hashes for {args.run_dir}.")

if __name__ == "__main__":
    main()
