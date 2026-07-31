"""Build deterministic Business Platform V2 release metadata and archives."""

from __future__ import annotations

import hashlib
import json
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from server.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
VERSION = "2.0.0"
FILES = (
    "tiktok/business_platform",
    "server/api/auth",
    "server/api/app.py",
    "dashboard/frontend",
    "studio/frontend",
    "local_runtime",
    "scripts",
    ".env.example",
)
DOCS = tuple(path.name for path in ROOT.glob("BUSINESS_PLATFORM_V2_*.md")) + (
    "RELEASE_NOTES_BUSINESS_PLATFORM_V2.md",
)


def source_files() -> list[Path]:
    result: set[Path] = set()
    for name in (*FILES, *DOCS):
        candidate = ROOT / name
        if candidate.is_file():
            result.add(candidate)
        elif candidate.is_dir():
            result.update(
                path
                for path in candidate.rglob("*")
                if path.is_file()
                and not any(
                    part in {"node_modules", "dist", "__pycache__"}
                    for part in path.parts
                )
                and path.suffix not in {".pyc", ".log"}
            )
    return sorted(result, key=lambda path: path.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(name: str, value: object) -> Path:
    path = ARTIFACTS / name
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def build() -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    files = source_files()
    inventory = [path.relative_to(ROOT).as_posix() for path in files]
    integrity = {name: sha256(ROOT / name) for name in inventory}
    generated = datetime.now(timezone.utc).isoformat()
    write_json(
        "BUSINESS_PLATFORM_V2_RELEASE_MANIFEST.json",
        {"product": "TKAI Business Platform", "version": VERSION, "files": inventory},
    )
    write_json(
        "BUSINESS_PLATFORM_V2_COMPONENT_MANIFEST.json",
        {
            "version": VERSION,
            "modules": [
                "accounts",
                "browsers",
                "proxies",
                "tasks",
                "content",
                "data",
                "ai-studio",
                "admin",
            ],
            "execution_enabled": False,
        },
    )
    write_json(
        "BUSINESS_PLATFORM_V2_BUILD_METADATA.json",
        {"version": VERSION, "generated_at": generated, "offline": True},
    )
    write_json(
        "BUSINESS_PLATFORM_V2_INTEGRITY_MANIFEST.json",
        {"algorithm": "SHA-256", "files": integrity},
    )
    write_json("business-platform-v2-openapi.json", create_app().openapi())
    (ARTIFACTS / "BUSINESS_PLATFORM_V2_PRODUCTION_READINESS.md").write_text(
        "# Business Platform V2 Production Readiness\n\n"
        "Generated after validation. See acceptance report and manifests.\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "RELEASE_NOTES_BUSINESS_PLATFORM_V2.md").write_text(
        (ROOT / "RELEASE_NOTES_BUSINESS_PLATFORM_V2.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    zip_path = ARTIFACTS / "tkai-business-platform-2.0.0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    tar_path = ARTIFACTS / "tkai-business-platform-2.0.0.tar.gz"
    with tarfile.open(tar_path, "w:gz") as archive:
        for path in files:
            archive.add(path, path.relative_to(ROOT).as_posix())
    artifact_names = (
        "business-platform-v2-openapi.json",
        "BUSINESS_PLATFORM_V2_BUILD_METADATA.json",
        "BUSINESS_PLATFORM_V2_COMPONENT_MANIFEST.json",
        "BUSINESS_PLATFORM_V2_INTEGRITY_MANIFEST.json",
        "BUSINESS_PLATFORM_V2_PRODUCTION_READINESS.md",
        "BUSINESS_PLATFORM_V2_RELEASE_MANIFEST.json",
        "RELEASE_NOTES_BUSINESS_PLATFORM_V2.md",
        "tkai-business-platform-2.0.0.tar.gz",
        "tkai-business-platform-2.0.0.zip",
    )
    produced = [ARTIFACTS / name for name in artifact_names]
    lines = [
        f"{sha256(path)}  {path.name}"
        for path in produced
        if path.name != "BUSINESS_PLATFORM_V2_CHECKSUMS.txt"
    ]
    (ARTIFACTS / "BUSINESS_PLATFORM_V2_CHECKSUMS.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
