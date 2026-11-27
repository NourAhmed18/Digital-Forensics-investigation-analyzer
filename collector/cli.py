"""Command-line interface for the collector agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import collect_case

DEFAULT_CONFIG = Path(__file__).with_name("collector_config.json")


def _load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a JSON object")
    modules = data.get("enabled_modules", ["host_info"])
    if not isinstance(modules, list) or not all(isinstance(item, str) for item in modules):
        raise ValueError("enabled_modules must be a list of strings")
    data["enabled_modules"] = modules
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forensic-collector",
        description="Create a hashed, structured evidence package from an authorized endpoint.",
    )
    parser.add_argument("--output", type=Path, default=Path("cases"), help="Directory that will contain the new case")
    parser.add_argument("--case-id", help="Optional case identifier; path separators are sanitized")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="JSON configuration file")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging on the console")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = _load_config(args.config)
        result = collect_case(args.output, args.case_id, config, args.config, args.verbose)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Collection failed: {exc}")
        return 1
    print(f"Case created: {result.case_dir}")
    print(f"Manifest: {result.manifest_path}")
    if result.skipped_modules:
        print("Skipped modules: " + ", ".join(result.skipped_modules))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
