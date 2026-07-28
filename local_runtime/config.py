"""Local-runtime configuration with loopback and bounded-path defaults."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when local-runtime configuration is unsafe or incomplete."""


@dataclass(frozen=True)
class LocalRuntimeConfig:
    """Validated settings for one local TKAI checkout."""

    repository: Path
    runtime_dir: Path
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 4173
    studio_host: str = "127.0.0.1"
    studio_port: int = 4174
    database_url: str = "sqlite:///runtime/data/tkai-local.db"
    mode: str = "production-local"
    secret_reference: str = "windows-credential-manager://TKAI/local"
    log_retention_days: int = 14
    backup_retention_count: int = 10
    max_browser_instances: int = 3
    max_tabs_per_browser: int = 5
    max_workflow_concurrency: int = 4
    max_publishing_concurrency: int = 2
    max_collection_concurrency: int = 3
    max_interaction_concurrency: int = 3
    max_queue_size: int = 1000
    max_payload_bytes: int = 2_097_152
    max_export_rows: int = 10_000
    max_query_rows: int = 1000

    @classmethod
    def load(cls, repository: Path, path: Path | None = None) -> LocalRuntimeConfig:
        """Load JSON configuration or return secure defaults."""
        repo = repository.resolve()
        source = path or repo / "configuration" / "local.json"
        values: dict[str, Any] = {}
        if source.exists():
            try:
                values = json.loads(source.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise ConfigurationError(
                    f"invalid configuration JSON: {error}"
                ) from error
        fields = cls.__dataclass_fields__
        for name in fields:
            environment = f"TKAI_{name.upper()}"
            if environment not in os.environ or name in {"repository", "runtime_dir"}:
                continue
            current = fields[name].default
            raw = os.environ[environment]
            values[name] = int(raw) if isinstance(current, int) else raw
        runtime_value = values.pop("runtime_dir", "runtime")
        runtime = Path(runtime_value)
        if not runtime.is_absolute():
            runtime = repo / runtime
        config = cls(repository=repo, runtime_dir=runtime.resolve(), **values)
        config.validate()
        return config

    def validate(self) -> None:
        """Reject public binding, traversal, invalid ports, and secret material."""
        if self.mode not in {"development", "production-local"}:
            raise ConfigurationError("mode must be development or production-local")
        allowed_hosts = {"127.0.0.1", "localhost", "::1"}
        for name, host in (
            ("backend_host", self.backend_host),
            ("dashboard_host", self.dashboard_host),
            ("studio_host", self.studio_host),
        ):
            if host not in allowed_hosts:
                raise ConfigurationError(
                    f"{name} requires explicit LAN opt-in; "
                    "local mode accepts loopback only"
                )
        ports = (self.backend_port, self.dashboard_port, self.studio_port)
        if any(port < 1024 or port > 65535 for port in ports) or len(set(ports)) != 3:
            raise ConfigurationError(
                "service ports must be unique and between 1024-65535"
            )
        if not _is_within(self.runtime_dir, self.repository):
            raise ConfigurationError("runtime_dir must remain inside the repository")
        if not self.secret_reference or "://" not in self.secret_reference:
            raise ConfigurationError(
                "secret_reference must name an external secret provider"
            )
        lowered = self.database_url.lower()
        if "password=" in lowered or "@" in self.database_url.split("://", 1)[-1]:
            raise ConfigurationError(
                "database_url must not embed plaintext credentials"
            )
        limits = (
            self.max_browser_instances,
            self.max_tabs_per_browser,
            self.max_workflow_concurrency,
            self.max_publishing_concurrency,
            self.max_collection_concurrency,
            self.max_interaction_concurrency,
            self.max_queue_size,
            self.max_payload_bytes,
            self.max_export_rows,
            self.max_query_rows,
        )
        if any(value <= 0 for value in limits):
            raise ConfigurationError("resource and concurrency limits must be positive")

    def public_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation without secret values."""
        result = asdict(self)
        result["repository"] = str(self.repository)
        result["runtime_dir"] = str(self.runtime_dir)
        result["secret_reference"] = "<configured-reference>"
        return result


def resolve_bounded(root: Path, child: str | Path) -> Path:
    """Resolve a child path and reject traversal outside root."""
    root_resolved = root.resolve()
    candidate = (root_resolved / child).resolve()
    if not _is_within(candidate, root_resolved):
        raise ConfigurationError(f"path escapes approved runtime directory: {child}")
    return candidate


def _is_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False
