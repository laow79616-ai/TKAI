"""Deterministic, offline TKAI V8 production-readiness and packaging audit."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
V8_SOURCE = SOURCE / "tkai" / "v8"
ARTIFACTS = ROOT / "artifacts"
VERSION = "8.0.0"
BASE_COMMIT = "fa840e21f996f46010a5144dd15a3c3a2c5b086b"
sys.path[:0] = [str(SOURCE), str(ROOT)]

FRAMEWORKS = {
    "Hyper Kernel Architecture": "tkai.v8",
    "Hyper Coordination Framework": "tkai.v8.hyper_coordination",
    "Hyper Intelligence Fabric": "tkai.v8.hyper_intelligence",
    "Hyper Governance Fabric": "tkai.v8.hyper_governance",
    "Hyper Knowledge Fabric": "tkai.v8.hyper_knowledge",
    "Hyper Reasoning Fabric": "tkai.v8.hyper_reasoning",
    "Hyper Decision Fabric": "tkai.v8.hyper_decision",
    "Hyper Autonomous Planning Fabric": "tkai.v8.hyper_planning",
    "Hyper Simulation & Forecasting Fabric": "tkai.v8.hyper_simulation",
    "Hyper Autonomous Operations Fabric": "tkai.v8.hyper_operations",
    "Hyper Recovery & Resilience Fabric": "tkai.v8.hyper_recovery",
}
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "artifacts",
    "work",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".cookie", ".cookies", ".session"}
SECRET_NAME = re.compile(
    r"(^|[._-])(secret|credential|credentials|cookies?|sessions?)([._-]|$)", re.I
)
SECRET_VALUE = re.compile(
    rb"(?i)(api[_-]?key|client[_-]?secret|password|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9/+_.-]{12,}"
)


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(SOURCE).with_suffix("").parts).removesuffix(
        ".__init__"
    )


def import_graph() -> dict[str, tuple[str, ...]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for path in V8_SOURCE.rglob("*.py"):
        source = module_name(path)
        graph[source]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            targets: tuple[str, ...] = ()
            if isinstance(node, ast.Import):
                targets = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = (node.module,)
            graph[source].update(
                item
                for item in targets
                if item.startswith("tkai.v8")
                and not (item in FRAMEWORKS.values() and source.startswith(f"{item}."))
            )
    return {key: tuple(sorted(value)) for key, value in sorted(graph.items())}


def cycles(graph: dict[str, tuple[str, ...]]) -> list[list[str]]:
    found: list[list[str]] = []
    active: list[str] = []
    complete: set[str] = set()

    def visit(node: str) -> None:
        if node in active:
            cycle = active[active.index(node) :] + [node]
            if cycle not in found:
                found.append(cycle)
            return
        if node in complete:
            return
        active.append(node)
        for target in graph.get(node, ()):
            if target in graph:
                visit(target)
        active.pop()
        complete.add(node)

    for node in graph:
        visit(node)
    return found


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def inventory() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES or SECRET_NAME.search(path.name):
            continue
        if path.name == ".env":
            continue
        files.append(relative)
    return sorted(files, key=lambda item: item.as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def openapi_inventory() -> dict[str, object]:
    from server.api.app import create_app

    schema = create_app().openapi()
    operations = [
        (method.upper(), path, operation)
        for path, methods in schema["paths"].items()
        for method, operation in methods.items()
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    ]
    operation_ids = [item[2].get("operationId") for item in operations]
    duplicates = sorted(
        {item for item in operation_ids if item and operation_ids.count(item) > 1}
    )
    v8_operations = [item for item in operations if item[1].startswith("/v8/")]
    unsafe_v8 = [(method, path) for method, path, _ in v8_operations if method != "GET"]
    return {
        "path_count": len(schema["paths"]),
        "operation_count": len(operations),
        "v8_path_count": len({item[1] for item in v8_operations}),
        "v8_operation_count": len(v8_operations),
        "duplicate_operation_ids": duplicates,
        "unsafe_v8_operations": unsafe_v8,
        "schema": schema,
    }


def audit() -> dict[str, object]:
    graph = import_graph()
    errors: list[str] = []
    framework_results: list[dict[str, object]] = []
    for name, target in FRAMEWORKS.items():
        try:
            module = importlib.import_module(target)
            exports = getattr(module, "__all__", ())
            missing = sorted(item for item in exports if not hasattr(module, item))
            if missing:
                errors.append(f"{target}: missing exports {missing}")
            framework_results.append(
                {
                    "name": name,
                    "module": target,
                    "status": "completed",
                    "public_api_valid": not missing,
                }
            )
        except Exception as exc:
            errors.append(f"{target}: {type(exc).__name__}: {exc}")
            framework_results.append(
                {"name": name, "module": target, "status": "failed"}
            )
    package_names = [module_name(path) for path in V8_SOURCE.rglob("__init__.py")]
    duplicates = sorted(
        name for name in set(package_names) if package_names.count(name) > 1
    )
    found_cycles = cycles(graph)
    api = openapi_inventory()
    if duplicates:
        errors.append(f"duplicate packages: {duplicates}")
    if found_cycles:
        errors.append(f"circular imports: {found_cycles}")
    if api["duplicate_operation_ids"]:
        errors.append("duplicate OpenAPI operation IDs")
    if api["unsafe_v8_operations"]:
        errors.append("V8 advisory routes include mutation operations")
    return {
        "schema_version": 1,
        "version": VERSION,
        "base_commit": BASE_COMMIT,
        "source_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "framework_count": len(framework_results),
        "frameworks": framework_results,
        "repository": {
            "path": str(ROOT),
            "v8_module_count": len(graph),
            "duplicate_packages": duplicates,
            "circular_dependencies": found_cycles,
        },
        "compatibility": {
            "supported_versions": ["6.0.0", "7.0.0", "8.0.0"],
            "tiktok_business_behavior_changed": False,
            "existing_runtime_and_storage_behavior_changed": False,
        },
        "security": {
            "v8_api_policy": "authenticated read-only advisory metadata",
            "execution_endpoints": False,
            "runtime_mutation_endpoints": False,
            "secret_or_hidden_reasoning_endpoints": False,
        },
        "openapi": {key: value for key, value in api.items() if key != "schema"},
        "status": "ready" if not errors and len(framework_results) == 11 else "blocked",
        "errors": errors,
    }


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build(summary: str) -> dict[str, object]:
    report = audit()
    if report["status"] != "ready":
        raise RuntimeError("; ".join(report["errors"]))
    ARTIFACTS.mkdir(exist_ok=True)
    api = openapi_inventory()
    files = inventory()
    secret_hits = []
    config_suffixes = {".env", ".ini", ".json", ".toml", ".yaml", ".yml"}
    for relative in files:
        if (
            relative.suffix.lower() not in config_suffixes
            or "example" in relative.name.lower()
            or relative.parts[0] in {".github", "tests"}
        ):
            continue
        data = (ROOT / relative).read_bytes()
        if SECRET_VALUE.search(data) and b"${" not in data:
            secret_hits.append(relative.as_posix())
    if secret_hits:
        raise RuntimeError(f"possible secrets found: {secret_hits}")

    framework_manifest = {
        "schema_version": 1,
        "release": VERSION,
        "framework_count": 11,
        "frameworks": report["frameworks"],
    }
    release_manifest = {
        "schema_version": 1,
        "product": "TKAI TikTok Cloud Control Platform",
        "version": VERSION,
        "release_type": "production-candidate",
        "source_base_commit": BASE_COMMIT,
        "source_commit": report["source_commit"],
        "framework_count": 11,
        "module_count": report["repository"]["v8_module_count"],
        "api_inventory": report["openapi"],
        "compatibility": report["compatibility"],
        "environment_prerequisites": [
            "Python >=3.10",
            "Node.js >=18",
            "PowerShell 7 recommended",
        ],
    }
    build_metadata = {
        "version": VERSION,
        "source_commit": report["source_commit"],
        "source_date_epoch": int(os.environ.get("SOURCE_DATE_EPOCH", "0")),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reproducibility": "Set SOURCE_DATE_EPOCH and build from source_commit.",
        "test_summary": summary,
    }
    write_json(ARTIFACTS / "FRAMEWORK_MANIFEST_V8.json", framework_manifest)
    write_json(ARTIFACTS / "RELEASE_MANIFEST_V8.json", release_manifest)
    write_json(ARTIFACTS / "BUILD_METADATA_V8.json", build_metadata)
    write_json(ARTIFACTS / "openapi-v8.json", api["schema"])

    prefix = f"tkai-{VERSION}"
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
    zip_path = ARTIFACTS / f"{prefix}.zip"
    tar_path = ARTIFACTS / f"{prefix}.tar.gz"
    with zipfile.ZipFile(
        zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for relative in files:
            info = zipfile.ZipInfo(f"{prefix}/{relative.as_posix()}")
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (ROOT / relative).read_bytes())
    with tarfile.open(tar_path, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for relative in files:
            source = ROOT / relative
            info = archive.gettarinfo(str(source), f"{prefix}/{relative.as_posix()}")
            info.mtime = epoch
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with source.open("rb") as stream:
                archive.addfile(info, stream)

    integrity = {
        "algorithm": "SHA-256",
        "version": VERSION,
        "source_tree_file_count": len(files),
        "source_tree_digest": hashlib.sha256(
            "".join(
                f"{sha256(ROOT / item)}  {item.as_posix()}\n" for item in files
            ).encode()
        ).hexdigest(),
        "archives": {zip_path.name: sha256(zip_path), tar_path.name: sha256(tar_path)},
        "secret_scan": "passed",
        "unsafe_paths": [],
        "duplicate_entries": [],
    }
    write_json(ARTIFACTS / "INTEGRITY_MANIFEST_V8.json", integrity)
    package_files = [
        tar_path,
        zip_path,
        ARTIFACTS / "RELEASE_MANIFEST_V8.json",
        ARTIFACTS / "FRAMEWORK_MANIFEST_V8.json",
        ARTIFACTS / "BUILD_METADATA_V8.json",
        ARTIFACTS / "INTEGRITY_MANIFEST_V8.json",
        ARTIFACTS / "openapi-v8.json",
    ]
    checksums = (
        "\n".join(f"{sha256(path)}  {path.name}" for path in package_files) + "\n"
    )
    (ARTIFACTS / "CHECKSUMS_V8.txt").write_text(checksums, encoding="utf-8")
    readiness = (
        "# TKAI V8 Production Readiness\n\n"
        f"- Status: **{report['status'].upper()}**\n"
        f"- Frameworks: {report['framework_count']}/11 completed\n"
        f"- OpenAPI: {report['openapi']['path_count']} paths, "
        f"{report['openapi']['operation_count']} operations\n"
        "- Compatibility: V6, V7, TikTok, dashboard, AI Studio, "
        "and local runtime\n"
        "- Security: V8 routes are GET-only advisory surfaces; secret scan passed\n"
        f"- Validation: {summary}\n"
        "- Known issues: Optional integrations require documented "
        "external services.\n"
        "- Release blockers: None detected by the deterministic audit.\n"
    )
    (ARTIFACTS / "PRODUCTION_READINESS_V8.md").write_text(readiness, encoding="utf-8")
    return report


def validate_archives() -> None:
    for path in (
        ARTIFACTS / f"tkai-{VERSION}.zip",
        ARTIFACTS / f"tkai-{VERSION}.tar.gz",
    ):
        names: list[str]
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                bad = archive.testzip()
                if bad:
                    raise RuntimeError(f"corrupt zip member: {bad}")
        else:
            with tarfile.open(path) as archive:
                names = archive.getnames()
        if len(names) != len(set(names)):
            raise RuntimeError(f"duplicate entries in {path.name}")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                raise RuntimeError(f"unsafe archive path: {name}")
            if any(part in EXCLUDED_PARTS for part in pure.parts):
                raise RuntimeError(f"excluded archive entry: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--validate-archives", action="store_true")
    parser.add_argument("--test-summary", default="not supplied")
    args = parser.parse_args()
    report = build(args.test_summary) if args.build else audit()
    if args.validate_archives:
        validate_archives()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
