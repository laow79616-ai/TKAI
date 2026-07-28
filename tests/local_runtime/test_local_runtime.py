from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from local_runtime.api import register_local_runtime_routes
from local_runtime.config import ConfigurationError, LocalRuntimeConfig, resolve_bounded
from local_runtime.manager import DIRECTORIES, SECRET_PATTERN, LocalRuntimeManager


def config(tmp_path: Path) -> LocalRuntimeConfig:
    (tmp_path / "tiktok" / "browser_runtime").mkdir(parents=True)
    return LocalRuntimeConfig(
        repository=tmp_path,
        runtime_dir=tmp_path / "runtime",
        database_url="sqlite:///runtime/data/tkai-local.db",
    )


def test_defaults_are_loopback_and_directories_are_bounded(tmp_path: Path) -> None:
    manager = LocalRuntimeManager(config(tmp_path))
    created = manager.initialize()
    assert set(created) == set(DIRECTORIES)
    assert manager.database_health()["healthy"] is True
    assert manager.config.backend_host == "127.0.0.1"


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        resolve_bounded(tmp_path / "runtime", "../private")


def test_public_binding_and_plaintext_database_secret_are_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(ConfigurationError):
        LocalRuntimeConfig(
            tmp_path, tmp_path / "runtime", backend_host="0.0.0.0"
        ).validate()
    with pytest.raises(ConfigurationError):
        LocalRuntimeConfig(
            tmp_path,
            tmp_path / "runtime",
            database_url="postgresql://user:password@example/db",
        ).validate()


def test_pid_references_are_repository_scoped(tmp_path: Path) -> None:
    manager = LocalRuntimeManager(config(tmp_path))
    manager.initialize()
    manager.write_pid("backend", 999999, "python server")
    assert manager.read_pid("backend")["pid"] == 999999  # type: ignore[index]
    path = tmp_path / "runtime/pids/backend.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["repository"] = "C:/other"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert manager.read_pid("backend") is None


def test_database_initialization_preserves_existing_data(tmp_path: Path) -> None:
    manager = LocalRuntimeManager(config(tmp_path))
    manager.initialize()
    database = manager.database_path()
    before = database.read_bytes()
    manager.initialize_database()
    assert database.read_bytes() == before


def test_backup_manifest_and_restore_validation(tmp_path: Path) -> None:
    manager = LocalRuntimeManager(config(tmp_path))
    backup = manager.backup()
    manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
    database = backup / "tkai-local.db"
    assert (
        manifest["files"]["tkai-local.db"]
        == hashlib.sha256(database.read_bytes()).hexdigest()
    )
    database.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="integrity"):
        manager.restore(backup, force=True)


def test_restore_preserves_external_secret_reference(tmp_path: Path) -> None:
    runtime_config = config(tmp_path)
    configuration = tmp_path / "configuration"
    configuration.mkdir()
    local_config = configuration / "local.json"
    local_config.write_text(
        json.dumps(
            {"secret_reference": "windows-credential-manager://TKAI/local"}
        ),
        encoding="utf-8",
    )
    manager = LocalRuntimeManager(runtime_config)
    backup = manager.backup()
    manager.restore(backup, force=True)
    restored = json.loads(local_config.read_text(encoding="utf-8"))
    assert (
        restored["secret_reference"]
        == "windows-credential-manager://TKAI/local"
    )


def test_diagnostic_secret_sanitization() -> None:
    value = "token=abc password:xyz cookie=qwe session=123 proxy_credentials=hidden"
    result = SECRET_PATTERN.sub(r"\1=<redacted>", value)
    assert "abc" not in result and "xyz" not in result and "hidden" not in result


def test_status_contract(tmp_path: Path) -> None:
    manager = LocalRuntimeManager(config(tmp_path))
    manager.initialize()
    status = manager.status()
    assert set(status["services"]) == {"backend", "dashboard", "studio"}
    assert status["database"]["healthy"] is True
    assert "runtime_directories" in status


def test_api_registration_uses_read_only_routes(tmp_path: Path) -> None:
    class App:
        def __init__(self) -> None:
            self.routes: list[tuple[str, list[str]]] = []

        def add_api_route(
            self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
        ) -> None:
            self.routes.append((path, methods))

    app = App()
    register_local_runtime_routes(app, tmp_path)
    assert app.routes == [
        ("/local-runtime/status", ["GET"]),
        ("/local-runtime/health", ["GET"]),
        ("/readiness", ["GET"]),
        ("/tiktok/system/health", ["GET"]),
    ]


def test_docker_compose_contract_is_loopback_and_persistent() -> None:
    repository = Path(__file__).resolve().parents[2]
    compose = yaml.safe_load(
        (repository / "docker-compose.local.yml").read_text(encoding="utf-8")
    )
    assert set(compose["services"]) == {"api", "dashboard", "studio"}
    assert "tkai-local-runtime" in compose["volumes"]
    assert all("healthcheck" in service for service in compose["services"].values())
    for service in compose["services"].values():
        assert service["ports"][0].startswith("127.0.0.1:")
