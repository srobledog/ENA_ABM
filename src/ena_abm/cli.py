from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ModelConfig
from .experiments import run_pilot
from .model import EntrepreneurialNetworkActivationModel


def _single(config_path: Path, output_path: Path | None) -> None:
    config = ModelConfig.from_dict(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    output = EntrepreneurialNetworkActivationModel(config).run()
    payload = json.dumps(output.summary, indent=2, sort_keys=True) + "\n"
    if output_path is None:
        print(payload, end="")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="ENA ABM v0.3")
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single", help="run one simulation")
    single.add_argument("--config", type=Path, required=True)
    single.add_argument("--output", type=Path)

    pilot = subparsers.add_parser("pilot", help="run the factorial pilot")
    pilot.add_argument("--config", type=Path, required=True)
    pilot.add_argument("--output-dir", type=Path, required=True)

    arguments = parser.parse_args()
    if arguments.command == "single":
        _single(arguments.config, arguments.output)
    else:
        result = run_pilot(arguments.config, arguments.output_dir)
        print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))


if __name__ == "__main__":
    main()
