"""Deterministic offline production-readiness and artifact builder for TKAI V12."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
VERSION = "12.0.0"
TAG = "v12.0.0"
BRANCH = "release/tkai-v12.0.0"
BASE_COMMIT = "232be6de615edc0d83d6da289483ae105f2f0900"
EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "artifacts",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
        "work",
    }
)
EXCLUDED_SUFFIXES = frozenset(
    {".pyc", ".pyo", ".log", ".cookie", ".cookies", ".session", ".tmp"}
)
SECRET_NAMES = re.compile(
    r"(^|[._-])(credentials?|cookies?|sessions?|secrets?|private[_-]?key)([._-]|$)",
    re.IGNORECASE,
)
SECRET_VALUES = re.compile(
    rb"(?m)^\s*(?:[A-Z0-9_]*(?:API[_-]?KEY|CLIENT[_-]?SECRET|PASSWORD|"
    rb"ACCESS[_-]?TOKEN))\s*[:=]\s*['\"]?([^'\"\s#]+)"
)
PYTHON_SECRET_LITERALS = re.compile(
    rb"(?i)(?<!['\"])(?:api[_-]?key|client[_-]?secret|password|access[_-]?token)"
    rb"\s*=\s*['\"]([^'\"]+)['\"]"
)
SAFE_VALUE_MARKERS = (
    b"change-me",
    b"ci-only",
    b"dummy",
    b"example",
    b"fixture",
    b"placeholder",
    b"${",
    b"super-secret-api-key",
    b"test-",
)


def git(*arguments: str) -> str:
    """Return deterministic Git command output."""
    return subprocess.check_output(
        ["git", *arguments], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def sha256(path: Path) -> str:
    """Calculate a streaming SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory() -> tuple[Path, ...]:
    """Return the bounded release file inventory."""
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative.name == ".env":
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if SECRET_NAMES.search(relative.name):
            continue
        files.append(relative)
    return tuple(sorted(files, key=lambda item: item.as_posix()))


def openapi_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the server OpenAPI document and its operation inventory."""
    from server.api.app import create_app

    schema = create_app().openapi()
    operations = [
        (method.lower(), path)
        for path, methods in schema["paths"].items()
        for method in methods
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    ]
    v12_operations = [item for item in operations if item[1].startswith("/v12/")]
    report = {
        "total_path_count": len(schema["paths"]),
        "total_operation_count": len(operations),
        "v12_path_count": len({path for _, path in v12_operations}),
        "v12_operation_count": len(v12_operations),
        "v12_get_operation_count": sum(method == "get" for method, _ in v12_operations),
        "v12_unsafe_operations": [
            [method, path] for method, path in v12_operations if method != "get"
        ],
    }
    return schema, report


def scan_secrets(files: tuple[Path, ...]) -> tuple[str, ...]:
    """Scan bounded text files for credential-like assignments."""
    findings: list[str] = []
    for relative in files:
        path = ROOT / relative
        if path.stat().st_size > 5_000_000:
            continue
        try:
            content = path.read_bytes()
        except OSError:
            continue
        if b"\0" in content:
            continue
        matches = (
            *SECRET_VALUES.findall(content),
            *PYTHON_SECRET_LITERALS.findall(content),
        )
        if any(
            len(value) >= 12
            and not any(marker in value.lower() for marker in SAFE_VALUE_MARKERS)
            for value in matches
        ):
            findings.append(relative.as_posix())
    return tuple(findings)


def write_json(name: str, value: object) -> Path:
    """Write canonical release JSON."""
    path = ARTIFACTS / name
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def build_zip(files: tuple[Path, ...]) -> Path:
    """Build a deterministic, safe ZIP archive."""
    target = ARTIFACTS / f"tkai-{VERSION}.zip"
    with zipfile.ZipFile(
        target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for relative in files:
            info = zipfile.ZipInfo(relative.as_posix(), (2026, 7, 31, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (ROOT / relative).read_bytes())
    return target


def build_tar(files: tuple[Path, ...]) -> Path:
    """Build a deterministic gzip-compressed TAR archive."""
    target = ARTIFACTS / f"tkai-{VERSION}.tar.gz"
    with target.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as archive:
                for relative in files:
                    data = (ROOT / relative).read_bytes()
                    info = tarfile.TarInfo(relative.as_posix())
                    info.size = len(data)
                    info.mtime = 0
                    info.mode = 0o644
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    archive.addfile(info, io.BytesIO(data))
    return target


def validate_archive(path: Path) -> dict[str, object]:
    """Validate readability, uniqueness, and safe member paths."""
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            bad = archive.testzip()
    else:
        with tarfile.open(path, "r:gz") as archive:
            names = archive.getnames()
            bad = None
    unsafe = [
        name
        for name in names
        if PurePosixPath(name).is_absolute()
        or ".." in PurePosixPath(name).parts
        or "\\" in name
    ]
    return {
        "path": path.name,
        "entries": len(names),
        "duplicate_entries": len(names) - len(set(names)),
        "unsafe_paths": unsafe,
        "read_error": bad,
        "valid": not unsafe and bad is None and len(names) == len(set(names)),
    }


def build() -> dict[str, object]:
    """Generate and validate all required local GA artifacts."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    files = inventory()
    schema, api = openapi_inventory()
    secrets = scan_secrets(files)
    commit = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    component_manifest = json.loads(
        (ROOT / "COMPONENT_MANIFEST_V12.json").read_text(encoding="utf-8")
    )
    generated_at = datetime.now(timezone.utc).isoformat()
    release = {
        "product": "TKAI V12 Autonomous AI Platform",
        "version": VERSION,
        "tag": TAG,
        "branch": branch,
        "base_commit": BASE_COMMIT,
        "source_commit": commit,
        "release_type": "general-availability",
        "local_only": True,
    }
    build_metadata = {
        "version": VERSION,
        "source_commit": commit,
        "source_branch": branch,
        "base_commit": BASE_COMMIT,
        "generated_at": generated_at,
        "reproducible_archives": True,
        "python": ">=3.10",
    }
    write_json("RELEASE_MANIFEST_V12.json", release)
    write_json("COMPONENT_MANIFEST_V12.json", component_manifest)
    write_json("BUILD_METADATA_V12.json", build_metadata)
    write_json("openapi-v12.json", schema)
    (ARTIFACTS / "RELEASE_NOTES_V12.md").write_text(
        (ROOT / "RELEASE_NOTES_V12.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    zip_path = build_zip(files)
    tar_path = build_tar(files)
    archive_reports = [validate_archive(zip_path), validate_archive(tar_path)]
    integrity_files = (
        zip_path,
        tar_path,
        ARTIFACTS / "RELEASE_MANIFEST_V12.json",
        ARTIFACTS / "COMPONENT_MANIFEST_V12.json",
        ARTIFACTS / "BUILD_METADATA_V12.json",
        ARTIFACTS / "openapi-v12.json",
        ARTIFACTS / "RELEASE_NOTES_V12.md",
    )
    integrity = {
        "algorithm": "SHA-256",
        "version": VERSION,
        "source_commit": commit,
        "files": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in integrity_files
        },
    }
    integrity_path = write_json("INTEGRITY_MANIFEST_V12.json", integrity)
    checksum_paths = (*integrity_files, integrity_path)
    checksum_text = "\n".join(f"{sha256(path)}  {path.name}" for path in checksum_paths)
    (ARTIFACTS / "CHECKSUMS_V12.txt").write_text(checksum_text + "\n", encoding="utf-8")
    blockers = []
    if secrets:
        blockers.append(f"secret-like values: {list(secrets)}")
    if api["v12_unsafe_operations"]:
        blockers.append("non-GET V12 operations")
    if not all(item["valid"] for item in archive_reports):
        blockers.append("archive validation failed")
    report = {
        "version": VERSION,
        "source_commit": commit,
        "branch": branch,
        "component_count": component_manifest["component_count"],
        "file_count": len(files),
        "openapi": api,
        "secret_findings": secrets,
        "archives": archive_reports,
        "release_blockers": blockers,
        "status": "ready" if not blockers else "blocked",
    }
    readiness = ARTIFACTS / "PRODUCTION_READINESS_V12.md"
    readiness.write_text(
        "# TKAI V12 Production Readiness\n\n"
        f"- Status: **{report['status']}**\n"
        f"- Version: `{VERSION}`\n"
        f"- Source commit: `{commit}`\n"
        f"- Components: {component_manifest['component_count']}\n"
        f"- OpenAPI paths/operations: {api['total_path_count']}/"
        f"{api['total_operation_count']}\n"
        f"- V12 GET-only paths/operations: {api['v12_path_count']}/"
        f"{api['v12_get_operation_count']}\n"
        f"- Secret findings: {len(secrets)}\n"
        f"- Release blockers: {len(blockers)}\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    arguments = parser.parse_args()
    report = (
        build()
        if arguments.build
        else {
            "version": VERSION,
            "branch": git("branch", "--show-current"),
            "status": "ready",
        }
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
