"""Command-line interface shared by native Windows scripts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import LocalRuntimeConfig
from .manager import LocalRuntimeManager


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m local_runtime.cli")
    parser.add_argument(
        "command", choices=("init", "status", "health", "backup", "restore", "diagnose")
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--include-media-manifest", action="store_true")
    args = parser.parse_args()
    manager = LocalRuntimeManager(LocalRuntimeConfig.load(args.repository, args.config))
    if args.command == "init":
        result = manager.initialize()
    elif args.command == "status":
        result = manager.status()
    elif args.command == "health":
        result = manager.health()
    elif args.command == "backup":
        result = {"backup": str(manager.backup(args.include_media_manifest))}
    elif args.command == "restore":
        if args.backup is None:
            parser.error("restore requires --backup")
        manager.restore(args.backup, args.force)
        result = {"restored": str(args.backup)}
    else:
        result = manager.diagnostics()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
