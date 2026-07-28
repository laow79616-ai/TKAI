"""Runtime state, health, backup, restore, and diagnostic operations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import sqlite3
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from .config import LocalRuntimeConfig, resolve_bounded

DIRECTORIES = (
    "data",
    "logs",
    "pids",
    "browser_profiles",
    "media",
    "exports",
    "backups",
    "temp",
)
SERVICES = ("backend", "dashboard", "studio")
TIKTOK_MODULES = (
    "account_center",
    "browser_runtime",
    "proxy_center",
    "account_farming",
    "content_center",
    "publishing_center",
    "data_collection",
    "interaction_center",
    "risk_control",
    "workflow_center",
    "operations_center",
    "analytics_center",
)
REQUIRED_ROUTES = ("/health", "/tiktok/accounts", "/tiktok/browser")
SECRET_PATTERN = re.compile(
    r"(?i)(password|secret|token|cookie|session|proxy[_-]?credentials)"
    r"\s*[:=]\s*[^\s,;]+"
)


class LocalRuntimeManager:
    """Own bounded local runtime state for a validated configuration."""

    def __init__(self, config: LocalRuntimeConfig) -> None:
        config.validate()
        self.config = config

    def initialize(self) -> dict[str, str]:
        """Create approved directories and a database without replacing data."""
        created: dict[str, str] = {}
        self.config.runtime_dir.mkdir(parents=True, exist_ok=True)
        for name in DIRECTORIES:
            path = resolve_bounded(self.config.runtime_dir, name)
            path.mkdir(parents=True, exist_ok=True)
            created[name] = str(path)
        self.initialize_database()
        return created

    def initialize_database(self) -> Path:
        """Create the local metadata database with idempotent migrations."""
        path = self.database_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(path, timeout=5) as database:
                integrity = database.execute("PRAGMA integrity_check").fetchone()
                if integrity != ("ok",):
                    raise RuntimeError("database integrity validation failed")
                database.execute(
                    "CREATE TABLE IF NOT EXISTS runtime_metadata "
                    "(key TEXT PRIMARY KEY, value TEXT NOT NULL, "
                    "updated_at TEXT NOT NULL)"
                )
                database.execute(
                    "INSERT OR IGNORE INTO runtime_metadata VALUES (?, ?, ?)",
                    ("schema_version", "1", _now()),
                )
        except sqlite3.OperationalError as error:
            raise RuntimeError(
                f"SQLite initialization failed (database may be locked): {error}"
            ) from error
        return path

    def database_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.config.database_url.startswith(prefix):
            raise ValueError("native local runtime currently requires a sqlite:/// URL")
        value = self.config.database_url[len(prefix) :]
        candidate = Path(value)
        if candidate.is_absolute():
            path = candidate.resolve()
        else:
            path = (self.config.repository / candidate).resolve()
        return resolve_bounded(
            self.config.runtime_dir, path.relative_to(self.config.runtime_dir)
        )

    def write_pid(self, service: str, pid: int, command: str) -> Path:
        """Record process identity used to prevent unrelated termination."""
        if service not in SERVICES or pid <= 0:
            raise ValueError("invalid service PID reference")
        path = resolve_bounded(self.config.runtime_dir, f"pids/{service}.json")
        payload = {
            "service": service,
            "pid": pid,
            "command": command,
            "repository": str(self.config.repository),
            "created_at": _now(),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def read_pid(self, service: str) -> dict[str, Any] | None:
        """Read only a correctly scoped PID reference."""
        if service not in SERVICES:
            raise ValueError("unknown service")
        path = resolve_bounded(self.config.runtime_dir, f"pids/{service}.json")
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if (
            payload.get("service") != service
            or payload.get("repository") != str(self.config.repository)
            or not isinstance(payload.get("pid"), int)
        ):
            return None
        return dict(payload)

    def status(self) -> dict[str, Any]:
        """Return the dashboard-safe local runtime contract."""
        services: dict[str, Any] = {}
        for service, host, port in (
            ("backend", self.config.backend_host, self.config.backend_port),
            ("dashboard", self.config.dashboard_host, self.config.dashboard_port),
            ("studio", self.config.studio_host, self.config.studio_port),
        ):
            pid_ref = self.read_pid(service)
            services[service] = {
                "status": "running"
                if pid_ref and _pid_exists(pid_ref["pid"]) and _port_open(host, port)
                else "stopped",
                "host": host,
                "port": port,
                "url": f"http://{host}:{port}",
                "pid": pid_ref["pid"] if pid_ref else None,
                "port_active": _port_open(host, port),
            }
        return {
            "mode": self.config.mode,
            "services": services,
            "database": self.database_health(),
            "browser_runtime": {
                "status": "registered"
                if (self.config.repository / "tiktok/browser_runtime").is_dir()
                else "missing"
            },
            "runtime_directories": {
                name: str(resolve_bounded(self.config.runtime_dir, name))
                for name in DIRECTORIES
            },
            "last_health_check": self._last_health(),
            "logs": str(resolve_bounded(self.config.runtime_dir, "logs")),
            "data": str(resolve_bounded(self.config.runtime_dir, "data")),
            "backup": self.last_backup(),
        }

    def health(self, probe_http: bool = True) -> dict[str, Any]:
        """Validate local dependencies without contacting TikTok."""
        checks: dict[str, Any] = {
            "configuration": _check(self.config.validate),
            "runtime_directories": all(
                resolve_bounded(self.config.runtime_dir, name).is_dir()
                for name in DIRECTORIES
            ),
            "database": self.database_health()["healthy"],
            "tiktok_modules": {
                name: (self.config.repository / "tiktok" / name).is_dir()
                for name in TIKTOK_MODULES
            },
            "required_routes": list(REQUIRED_ROUTES),
        }
        if probe_http:
            checks["http"] = {
                "backend": _http_ok(
                    f"http://{self.config.backend_host}:{self.config.backend_port}/health"
                ),
                "dashboard": _http_ok(
                    f"http://{self.config.dashboard_host}:{self.config.dashboard_port}"
                ),
                "studio": _http_ok(
                    f"http://{self.config.studio_host}:{self.config.studio_port}"
                ),
            }
        healthy = (
            checks["configuration"]
            and checks["runtime_directories"]
            and checks["database"]
            and all(checks["tiktok_modules"].values())
            and (not probe_http or all(checks["http"].values()))
        )
        result = {"healthy": healthy, "checked_at": _now(), "checks": checks}
        target = resolve_bounded(self.config.runtime_dir, "logs/last-health.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2), encoding="utf-8")
        self._operation_log("health", result)
        return result

    def database_health(self) -> dict[str, Any]:
        try:
            with sqlite3.connect(self.database_path()) as database:
                row = database.execute("PRAGMA integrity_check").fetchone()
            return {
                "healthy": row == ("ok",),
                "engine": "sqlite",
                "path": str(self.database_path()),
            }
        except (OSError, sqlite3.Error, ValueError) as error:
            return {"healthy": False, "engine": "sqlite", "error": str(error)}

    def backup(self, include_media_manifest: bool = False) -> Path:
        """Create a timestamped backup plus SHA-256 integrity manifest."""
        self.initialize()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = resolve_bounded(self.config.runtime_dir, f"backups/{stamp}")
        target.mkdir(parents=True)
        shutil.copy2(self.database_path(), target / "tkai-local.db")
        config_source = self.config.repository / "configuration" / "local.json"
        if config_source.exists():
            data = json.loads(config_source.read_text(encoding="utf-8"))
            data["secret_reference"] = "<configured-reference>"
            (target / "local.json").write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        metadata = {
            "created_at": _now(),
            "mode": self.config.mode,
            "secret_reference": "<redacted>",
        }
        (target / "runtime-metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        if include_media_manifest:
            media = resolve_bounded(self.config.runtime_dir, "media")
            files = [
                str(path.relative_to(media))
                for path in media.rglob("*")
                if path.is_file()
            ]
            (target / "media-manifest.json").write_text(
                json.dumps(files, indent=2), encoding="utf-8"
            )
        self._write_manifest(target)
        self._apply_retention()
        self._audit("backup", {"backup": target.name})
        self._operation_log("backup", {"backup": target.name})
        return target

    def restore(self, backup: Path, force: bool = False) -> None:
        """Validate and restore an explicit inactive backup."""
        backup = backup.resolve()
        backups_root = resolve_bounded(self.config.runtime_dir, "backups")
        backup.relative_to(backups_root)
        for service in SERVICES:
            reference = self.read_pid(service)
            if reference is not None and _pid_exists(reference["pid"]):
                raise RuntimeError("stop TKAI services before restore")
        if not force:
            raise RuntimeError("restore requires explicit force confirmation")
        self._validate_manifest(backup)
        safety = self.backup()
        shutil.copy2(backup / "tkai-local.db", self.database_path())
        config_backup = backup / "local.json"
        if config_backup.exists():
            destination = self.config.repository / "configuration" / "local.json"
            shutil.copy2(config_backup, destination)
        self._audit("restore", {"backup": backup.name, "safety_backup": safety.name})
        self._operation_log(
            "restore", {"backup": backup.name, "safety_backup": safety.name}
        )

    def diagnostics(self) -> dict[str, Any]:
        """Collect bounded, sanitized diagnostic information."""
        logs: dict[str, list[str]] = {}
        log_dir = resolve_bounded(self.config.runtime_dir, "logs")
        for path in list(log_dir.glob("*.log"))[:20]:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[
                -100:
            ]
            logs[path.name] = [
                SECRET_PATTERN.sub(r"\1=<redacted>", line) for line in lines
            ]
        return {
            "collected_at": _now(),
            "python": sys.version,
            "platform": sys.platform,
            "status": self.status(),
            "health": self.health(probe_http=False),
            "frontend_builds": {
                "dashboard": (
                    self.config.repository / "dashboard/frontend/dist"
                ).is_dir(),
                "studio": (self.config.repository / "studio/frontend/dist").is_dir(),
            },
            "logs": logs,
        }

    def _write_manifest(self, target: Path) -> None:
        entries = {}
        for path in sorted(target.iterdir()):
            if path.name != "manifest.json" and path.is_file():
                entries[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        (target / "manifest.json").write_text(
            json.dumps({"algorithm": "sha256", "files": entries}, indent=2),
            encoding="utf-8",
        )

    def _validate_manifest(self, target: Path) -> None:
        manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        for name, expected in manifest["files"].items():
            path = target / name
            if (
                not path.is_file()
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected
            ):
                raise RuntimeError(f"backup integrity validation failed: {name}")

    def _apply_retention(self) -> None:
        root = resolve_bounded(self.config.runtime_dir, "backups")
        backups = sorted(
            (path for path in root.iterdir() if path.is_dir()), reverse=True
        )
        for path in backups[self.config.backup_retention_count :]:
            shutil.rmtree(path)

    def _audit(self, action: str, detail: dict[str, Any]) -> None:
        path = resolve_bounded(self.config.runtime_dir, "logs/audit.jsonl")
        record = {"time": _now(), "action": action, **detail}
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")

    def _operation_log(self, operation: str, detail: dict[str, Any]) -> None:
        path = resolve_bounded(self.config.runtime_dir, f"logs/{operation}.jsonl")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"time": _now(), **detail}) + "\n")

    def _last_health(self) -> dict[str, Any] | None:
        path = resolve_bounded(self.config.runtime_dir, "logs/last-health.json")
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def last_backup(self) -> str | None:
        root = resolve_bounded(self.config.runtime_dir, "backups")
        if not root.exists():
            return None
        backups = sorted(path.name for path in root.iterdir() if path.is_dir())
        return backups[-1] if backups else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, PermissionError):
        return False


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _http_ok(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:  # noqa: S310 - loopback is validated
            return bool(200 <= response.status < 400)
    except OSError:
        return False


def _check(callback: Callable[[], None]) -> bool:
    try:
        callback()
        return True
    except (ValueError, OSError):
        return False
