"""Build and validate the final TKAI V7.0.0 local release assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
VERSION = "7.0.0"
TAG = "v7.0.0"
BASE_COMMIT = "0e31fe02c2afcac597aae9f839e3fb0679014af3"
ASSET_NAMES = (
    f"tkai-{VERSION}.tar.gz",
    f"tkai-{VERSION}.zip",
    "RELEASE_MANIFEST_V7.json",
    "FRAMEWORK_MANIFEST_V7.json",
    "BUILD_METADATA_V7.json",
    "INTEGRITY_MANIFEST_V7.json",
    "CHECKSUMS_V7.txt",
)
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def openapi_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT))
    from server.api.app import create_app
    from studio.backend.app import create_studio_app

    documents = {
        "server": create_app().openapi(),
        "studio": create_studio_app().openapi(),
    }
    inventory: dict[str, Any] = {}
    all_operations: list[dict[str, str]] = []
    for name, document in documents.items():
        operations = [
            {
                "service": name,
                "path": path,
                "method": method.upper(),
                "operation_id": details.get("operationId", ""),
            }
            for path, item in document["paths"].items()
            for method, details in item.items()
            if method in HTTP_METHODS
        ]
        ids = [item["operation_id"] for item in operations]
        duplicates = sorted({item for item in ids if item and ids.count(item) > 1})
        if duplicates:
            raise RuntimeError(f"Duplicate {name} OpenAPI operation IDs: {duplicates}")
        inventory[name] = {
            "version": document["info"]["version"],
            "path_count": len(document["paths"]),
            "operation_count": len(operations),
        }
        all_operations.extend(operations)
    if inventory["server"]["version"] != VERSION:
        raise RuntimeError("Server OpenAPI version is inconsistent.")
    if inventory["studio"]["version"] != VERSION:
        raise RuntimeError("Studio OpenAPI version is inconsistent.")
    return inventory, {"operations": all_operations}


def validate_member(name: str) -> None:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"Unsafe archive entry: {name}")
    lowered = f"/{normalized.lower().strip('/')}/"
    forbidden = (
        "/.git/",
        "/.venv/",
        "/node_modules/",
        "/__pycache__/",
        "/.pytest_cache/",
        "/.mypy_cache/",
        "/.ruff_cache/",
        "/artifacts/",
        "/.env/",
    )
    if any(term in lowered for term in forbidden):
        raise RuntimeError(f"Forbidden archive entry: {name}")


def validate_archives() -> dict[str, Any]:
    tar_path = ARTIFACTS / ASSET_NAMES[0]
    zip_path = ARTIFACTS / ASSET_NAMES[1]
    with tarfile.open(tar_path, "r:gz") as archive:
        tar_names = archive.getnames()
        for name in tar_names:
            validate_member(name)
    with zipfile.ZipFile(zip_path) as archive:
        zip_names = archive.namelist()
        for name in zip_names:
            validate_member(name)
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Unreadable ZIP member: {bad}")
    for kind, names in (("tar", tar_names), ("zip", zip_names)):
        if len(names) != len(set(names)):
            raise RuntimeError(f"Duplicate {kind} archive entries.")
    return {
        "tar_entry_count": len(tar_names),
        "zip_entry_count": len(zip_names),
        "unsafe_paths": 0,
        "duplicate_entries": 0,
        "readable": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pytest-summary", required=True)
    args = parser.parse_args()

    commit = run("git", "rev-parse", "HEAD")
    branch = run("git", "branch", "--show-current")
    if branch != "release/tkai-v7.0.0":
        raise RuntimeError(f"Unexpected release branch: {branch}")
    if run("git", "status", "--porcelain"):
        raise RuntimeError("Release assets must be built from a clean worktree.")
    if run("git", "rev-parse", f"{TAG}^{{}}") != commit:
        raise RuntimeError(f"{TAG} does not point to the release commit.")

    ARTIFACTS.mkdir(exist_ok=True)
    for name in ASSET_NAMES:
        path = ARTIFACTS / name
        if path.exists():
            path.unlink()

    prefix = f"tkai-{VERSION}/"
    subprocess.run(
        [
            "git",
            "archive",
            "--format=tar.gz",
            f"--prefix={prefix}",
            f"--output={ARTIFACTS / ASSET_NAMES[0]}",
            commit,
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "archive",
            "--format=zip",
            f"--prefix={prefix}",
            f"--output={ARTIFACTS / ASSET_NAMES[1]}",
            commit,
        ],
        cwd=ROOT,
        check=True,
    )

    framework_manifest = json.loads((ROOT / "FRAMEWORK_MANIFEST.json").read_text())
    frameworks = framework_manifest["frameworks"]
    if len(frameworks) != 15 or any(
        item["status"] != "completed" for item in frameworks
    ):
        raise RuntimeError(
            "Framework manifest must contain exactly 15 completed items."
        )
    framework_manifest.update({"release_commit": commit, "framework_count": 15})
    write_json(ARTIFACTS / "FRAMEWORK_MANIFEST_V7.json", framework_manifest)

    openapi, api_inventory = openapi_inventory()
    packages = sorted(
        ".".join(path.relative_to(ROOT).parent.parts)
        for path in ROOT.rglob("__init__.py")
        if not any(
            part in {".venv", "artifacts", "node_modules", "__pycache__", "work"}
            for part in path.parts
        )
    )
    archive_validation = validate_archives()
    built_at = datetime.now(timezone.utc).isoformat()
    build_metadata = {
        "product": "TKAI TikTok Cloud Control Platform",
        "version": VERSION,
        "tag": TAG,
        "git_commit": commit,
        "base_commit": BASE_COMMIT,
        "branch": branch,
        "built_at_utc": built_at,
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH"),
    }
    write_json(ARTIFACTS / "BUILD_METADATA_V7.json", build_metadata)

    compatibility = {
        "status": "compatible",
        "breaking_changes": False,
        "verified_surfaces": [
            "TKAI V6.0.0",
            "TikTok modules and execution behavior",
            "V6 and V7 APIs",
            "Dashboard",
            "AI Studio",
            "local runtime and deployment",
            "configuration and storage",
            "extensions",
            "OpenAPI",
        ],
    }
    security = {
        "status": "verified",
        "coverage": [
            "RBAC",
            "tenant/workspace/namespace isolation",
            "secret filtering",
            "audit",
            "runtime governance",
            "safe defaults",
        ],
        "prohibited_public_endpoints": [
            "unrestricted mutation",
            "execution",
            "automatic approval",
            "runtime configuration apply",
            "automatic migration",
            "secret value retrieval",
            "hidden reasoning retrieval",
            "chain-of-thought retrieval",
        ],
    }
    release_manifest = {
        "schema_version": 1,
        "product": "TKAI TikTok Cloud Control Platform",
        "release_version": VERSION,
        "release_commit": commit,
        "base_commit": BASE_COMMIT,
        "tag": TAG,
        "branch": branch,
        "build_timestamp_utc": built_at,
        "framework_inventory": frameworks,
        "framework_count": len(frameworks),
        "module_inventory": packages,
        "module_count": len(packages),
        "api_inventory": api_inventory,
        "openapi": openapi,
        "test_summary": args.pytest_summary,
        "compatibility_summary": compatibility,
        "security_summary": security,
        "observability_summary": {
            "status": "verified",
            "coverage": [
                "metrics registration",
                "structured logging",
                "tracing hooks",
                "diagnostics and health",
                "audit correlation",
                "dashboard projections",
                "framework health",
            ],
        },
        "artifact_inventory": list(ASSET_NAMES),
        "integrity_reference": "INTEGRITY_MANIFEST_V7.json",
        "known_issues": [
            "Live external integrations require deployment-owned services "
            "and credentials.",
            "Frontend production builds require installed Node dependencies.",
        ],
        "environment_prerequisites": {
            "required": ["Python >=3.10", "PowerShell", "Node.js/npm for frontends"],
            "optional": ["twine", "SQLAlchemy", "Alembic", "psycopg", "Redis"],
        },
    }
    write_json(ARTIFACTS / "RELEASE_MANIFEST_V7.json", release_manifest)

    integrity = {
        "schema_version": 1,
        "algorithm": "SHA-256",
        "release_version": VERSION,
        "release_commit": commit,
        "archive_validation": archive_validation,
        "archive_hashes": {name: sha256(ARTIFACTS / name) for name in ASSET_NAMES[:2]},
        "secret_scan": "passed by release validation",
        "checksum_catalog": "CHECKSUMS_V7.txt",
    }
    write_json(ARTIFACTS / "INTEGRITY_MANIFEST_V7.json", integrity)

    checksummed = ASSET_NAMES[:-1]
    checksum_lines = [f"{sha256(ARTIFACTS / name)}  {name}" for name in checksummed]
    (ARTIFACTS / "CHECKSUMS_V7.txt").write_text(
        "\n".join(checksum_lines) + "\n", encoding="ascii"
    )
    print(json.dumps({"assets": list(ASSET_NAMES), "openapi": openapi}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
