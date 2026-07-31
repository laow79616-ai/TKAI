from __future__ import annotations

import json
from pathlib import Path

import pytest

import tkai
from local_runtime.config import ConfigurationError, LocalRuntimeConfig
from local_runtime.integration import MODULES, integration_readiness, module_registry
from tiktok import TIKTOK_MODULE_KEYS, TIKTOK_MODULES


def test_registry_is_complete_unique_and_importable() -> None:
    registry = module_registry()
    assert tuple(item.key for item in registry) == tuple(key for key, _ in MODULES)
    assert len({item.key for item in registry}) == len(MODULES)
    assert all(item.registered for item in registry)
    assert TIKTOK_MODULE_KEYS == tuple(module.key for module in TIKTOK_MODULES)


def test_integration_health_detects_duplicate_routes(tmp_path: Path) -> None:
    class Route:
        path = "/duplicate"
        methods = {"GET"}

    class App:
        routes = [Route(), Route()]

    (tmp_path / "dashboard/frontend").mkdir(parents=True)
    (tmp_path / "studio/frontend").mkdir(parents=True)
    (tmp_path / "runtime/data").mkdir(parents=True)
    result = integration_readiness(App(), tmp_path)
    assert result["status"] == "not_ready"
    assert result["duplicate_routes"] == ["GET /duplicate"]
    assert result["live_tiktok_required"] is False


def test_application_registers_every_v6_module_without_duplicate_routes() -> None:
    from server.api.app import create_app

    root = Path(__file__).resolve().parents[2]
    result = integration_readiness(create_app(), root)
    assert len(result["modules"]) == len(TIKTOK_MODULES)
    assert all(item["registered"] for item in result["modules"])
    assert result["duplicate_routes"] == []


def test_environment_override_and_resource_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TKAI_MAX_BROWSER_INSTANCES", "2")
    config = LocalRuntimeConfig.load(tmp_path)
    assert config.max_browser_instances == 2
    with pytest.raises(ConfigurationError, match="positive"):
        LocalRuntimeConfig(tmp_path, tmp_path / "runtime", max_queue_size=0).validate()


def test_release_metadata_and_checklist_are_machine_readable() -> None:
    root = Path(__file__).resolve().parents[2]
    metadata = json.loads((root / "release.json").read_text(encoding="utf-8"))
    checklist = json.loads(
        (root / "release-checklist.json").read_text(encoding="utf-8")
    )
    assert metadata["version"] == tkai.__version__
    assert {"openapi", "backup", "restore", "secret_scan", "checksums"} <= set(
        checklist["checks"]
    )


def test_release_scripts_define_private_data_exclusions() -> None:
    root = Path(__file__).resolve().parents[2]
    build = (root / "scripts/build-release.ps1").read_text(encoding="utf-8").lower()
    validate = (
        (root / "scripts/validate-release.ps1").read_text(encoding="utf-8").lower()
    )
    forbidden_entries = (
        "node_modules",
        ".venv",
        ".db",
        "cookie",
        "session",
        "credential",
    )
    for forbidden in forbidden_entries:
        assert forbidden in build or forbidden in validate
    for required in (
        "release_manifest.json",
        "build_metadata.json",
        "sha256sums",
        "sourcearchive",
    ):
        assert required in build or required in validate
