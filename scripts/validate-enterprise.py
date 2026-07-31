"""Run local enterprise quality gates without publishing."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
SECRET = re.compile(
    rb"(?im)^\s*[A-Z0-9_]*(?:API[_-]?KEY|PASSWORD|CLIENT[_-]?SECRET|"
    rb"ACCESS[_-]?TOKEN)\s*[:=]\s*(?:['\"]([^'\"]+)['\"]|([A-Za-z0-9_-]+))"
)
SAFE = (
    b"example",
    b"placeholder",
    b"change-me",
    b"dummy",
    b"test-",
    b"ci-only",
    b"super-secret-api-key",
    b"${",
)


def run(name: str, command: list[str], cwd: Path = ROOT) -> dict[str, object]:
    """Run a command gate and return evidence."""
    print(f"==> {name}", flush=True)
    result = subprocess.run(command, cwd=cwd, check=False)
    return {
        "name": name,
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
    }


def import_gate() -> dict[str, object]:
    """Validate supported top-level imports."""
    try:
        for module in ("tkai", "server.api.app", "tiktok"):
            importlib.import_module(module)
    except Exception as exc:
        return {"name": "Import validation", "status": "failed", "detail": repr(exc)}
    return {"name": "Import validation", "status": "passed"}


def secret_gate() -> dict[str, object]:
    """Scan tracked text files for credential-like assignments."""
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    findings: list[str] = []
    for raw in tracked:
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        content = path.read_bytes()
        if b"\0" in content:
            continue
        values = tuple(quoted or plain for quoted, plain in SECRET.findall(content))
        if any(
            len(value) >= 12
            and not re.fullmatch(rb"[A-Za-z_][A-Za-z0-9_.()]*", value)
            and not any(marker in value.lower() for marker in SAFE)
            for value in values
        ):
            findings.append(relative.as_posix())
    return {
        "name": "Secret scanning",
        "status": "passed" if not findings else "failed",
        "findings": findings,
    }


def archive_gate() -> dict[str, object]:
    """Verify existing v12 release archives without regenerating them."""
    failures: list[str] = []
    checked: list[str] = []
    for path in sorted(ARTIFACTS.glob("tkai-12.0.0*")):
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                if archive.testzip():
                    failures.append(path.name)
        elif path.name.endswith(".tar.gz"):
            with tarfile.open(path, "r:gz") as archive:
                names = archive.getnames()
        else:
            continue
        checked.append(path.name)
        unsafe = any(
            PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or "\\" in name
            for name in names
        )
        if unsafe or len(names) != len(set(names)):
            failures.append(path.name)
    return {
        "name": "Archive validation",
        "status": "passed" if checked and not failures else "failed",
        "checked": checked,
        "failures": sorted(set(failures)),
    }


def openapi_gate() -> dict[str, object]:
    """Validate that the application produces a non-empty OpenAPI 3 document."""
    from server.api.app import create_app

    schema = create_app().openapi()
    paths = schema.get("paths", {})
    operations = sum(
        method.lower() in {"get", "post", "put", "patch", "delete"}
        for methods in paths.values()
        for method in methods
    )
    valid = str(schema.get("openapi", "")).startswith("3.") and bool(paths)
    return {
        "name": "OpenAPI validation",
        "status": "passed" if valid else "failed",
        "paths": len(paths),
        "operations": operations,
    }


def main() -> int:
    """Execute all enterprise gates and write a JSON report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-frontends", action="store_true")
    args = parser.parse_args()
    python = sys.executable
    gates = [
        run("Ruff", [python, "-m", "ruff", "check", "."]),
        run("mypy", [python, "-m", "mypy"]),
        run("pytest", [python, "-m", "pytest"]),
        run("Vulture", [python, "-m", "vulture"]),
        import_gate(),
        run("Dependency validation", [python, "-m", "pip", "check"]),
        run("Security validation", [python, "-m", "pip_audit", "--local"]),
        run("Package validation", [python, "-m", "build", "--outdir", "dist"]),
        archive_gate(),
        secret_gate(),
        openapi_gate(),
    ]
    if not args.skip_frontends:
        npm = "npm.cmd" if os.name == "nt" else "npm"
        gates.extend(
            (
                run(
                    "Dashboard build",
                    [npm, "run", "build"],
                    ROOT / "dashboard/frontend",
                ),
                run(
                    "AI Studio build",
                    [npm, "run", "build"],
                    ROOT / "studio/frontend",
                ),
            )
        )
    ARTIFACTS.mkdir(exist_ok=True)
    status = "passed" if all(gate["status"] == "passed" for gate in gates) else "failed"
    report = {"status": status, "gates": gates}
    (ARTIFACTS / "enterprise-validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
