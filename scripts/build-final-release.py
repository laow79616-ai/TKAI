"""Compatibility entry point for the TKAI V8.0.0 final release builder."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def load_builder():
    path = Path(__file__).with_name("verify-v8-production.py")
    spec = importlib.util.spec_from_file_location("verify_v8_production", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load release builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pytest-summary", required=True)
    args = parser.parse_args()
    builder = load_builder()
    builder.build(args.pytest_summary)
    builder.validate_archives()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
