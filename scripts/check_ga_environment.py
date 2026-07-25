#!/usr/bin/env python3
"""Report whether this host can run Marketplace Server V2 external GA checks."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Status = Literal["PASS", "FAIL", "WARNING"]
ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Check:
    """One deterministic prerequisite check without changing host state."""

    status: Status
    name: str
    detail: str
    required: bool = True


def command_version(command: tuple[str, ...]) -> str | None:
    """Return the first version line when a command is executable."""
    if shutil.which(command[0]) is None:
        return None
    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        return None
    return (completed.stdout or completed.stderr).strip().splitlines()[0]


def command_check(name: str, command: tuple[str, ...]) -> Check:
    """Check command availability without assuming a particular platform."""
    version = command_version(command)
    if version is None:
        return Check("FAIL", name, "not available")
    return Check("PASS", name, version)


def module_check(name: str) -> Check:
    """Check an installed Python module without importing application state."""
    if importlib.util.find_spec(name) is None:
        return Check("FAIL", f"Python module: {name}", "not installed")
    return Check("PASS", f"Python module: {name}", "available")


def file_check(name: str, relative_path: str, *, required: bool = True) -> Check:
    """Check a repository prerequisite path."""
    path = ROOT / relative_path
    if path.exists():
        return Check("PASS", name, relative_path, required)
    status: Status = "FAIL" if required else "WARNING"
    return Check(status, name, f"missing: {relative_path}", required)


def docker_daemon_check() -> Check:
    """Confirm the Docker CLI can reach a daemon without exposing configuration."""
    if shutil.which("docker") is None:
        return Check("FAIL", "Docker daemon", "Docker CLI is not available")
    completed = subprocess.run(
        ("docker", "info"),
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )
    if completed.returncode != 0:
        return Check("FAIL", "Docker daemon", "not reachable")
    return Check("PASS", "Docker daemon", "reachable")


def collect_checks() -> tuple[Check, ...]:
    """Collect all declared GA prerequisites without modifying files or services."""
    python_version = sys.version_info
    python_status: Status = "PASS" if python_version >= (3, 10) else "FAIL"
    venv_status: Status = "PASS" if sys.prefix != sys.base_prefix else "FAIL"
    checks: list[Check] = [
        Check(
            python_status,
            "Python >= 3.10",
            f"{python_version.major}.{python_version.minor}.{python_version.micro}",
        ),
        Check(
            venv_status,
            "Virtual environment",
            "active" if venv_status == "PASS" else "not active",
        ),
        module_check("build"),
        module_check("twine"),
        module_check("fastapi"),
        module_check("sqlalchemy"),
        module_check("alembic"),
        module_check("psycopg"),
        command_check("Node.js", ("node", "--version")),
        command_check("npm", ("npm", "--version")),
        command_check("Docker CLI", ("docker", "--version")),
        command_check("Docker Compose", ("docker", "compose", "version")),
        docker_daemon_check(),
        file_check("Dashboard package manifest", "dashboard/frontend/package.json"),
        file_check("Dashboard lockfile", "dashboard/frontend/package-lock.json"),
        file_check("Docker Compose configuration", "docker-compose.yml"),
        file_check("Alembic configuration", "server/persistence/alembic.ini"),
    ]
    return tuple(checks)


def main() -> int:
    """Print stable PASS/FAIL/WARNING output and return a meaningful status."""
    checks = collect_checks()
    for check in checks:
        print(f"{check.status:<7} {check.name}: {check.detail}")
    failed = any(check.required and check.status == "FAIL" for check in checks)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
