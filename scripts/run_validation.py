from __future__ import annotations

import argparse
import json
from pathlib import Path

from ena_abm.validation import run_validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ENA ABM v0.3 validation")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    result = run_validation(arguments.config, arguments.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

