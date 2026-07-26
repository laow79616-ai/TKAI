"""Sprint-5 Enterprise Plugin Marketplace coverage."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tkai.core.exceptions import PluginError
from tkai.plugins import (
    EnterprisePluginMarketplace,
    ExecutionLimits,
    MarketplacePluginLoader,
    MarketplaceRegistry,
    PermissionPolicy,
    PluginCatalog,
    PluginDefinition,
    PluginDependency,
    PluginPermission,
    PluginSandbox,
    PluginSigner,
    PluginState,
    SandboxPolicy,
)
from tkai.plugins.api import PluginApi, register_plugin_routes
from tkai.plugins.signing import checksum


def definition(
    version: str = "1.0.0",
    *,
    plugin_id: str = "acme.tools",
    dependencies: tuple[PluginDependency, ...] = (),
    permissions: frozenset[str] = frozenset(),
) -> PluginDefinition:
    return PluginDefinition(
        plugin_id,
        "Acme Tools",
        version,
        "Acme",
        "Enterprise tools",
        "https://example.test/plugins/acme-tools",
        "Apache-2.0",
        dependencies,
        permissions,
        ("summarize",),
        {"tier": "enterprise"},
        category="productivity",
        tags=frozenset({"agent", "workflow"}),
    )


def marketplace() -> EnterprisePluginMarketplace:
    return EnterprisePluginMarketplace(
        permission_policy=PermissionPolicy(
            frozenset({PluginPermission.WORKFLOW, PluginPermission.AGENT})
        ),
        clock=lambda: 100.0,
    )


def test_catalog_search_categories_and_tags() -> None:
    catalog = PluginCatalog()
    catalog.publish(definition())
    assert catalog.get("acme.tools").version == "1.0.0"
    assert catalog.search("enterprise", category="productivity", tag="agent")
    assert catalog.categories() == ("productivity",)
    assert catalog.tags() == ("agent", "workflow")


def test_registry_install_lifecycle_upgrade_rollback_and_uninstall() -> None:
    store = marketplace()
    store.register(definition())
    store.register(definition("2.0.0"))
    installed = store.install("acme.tools", "1.0.0")
    assert installed.state is PluginState.INSTALLED
    assert store.enable("acme.tools").state is PluginState.ENABLED
    assert store.disable("acme.tools").state is PluginState.DISABLED
    assert store.upgrade("acme.tools").definition.version == "2.0.0"
    assert store.rollback("acme.tools").definition.version == "1.0.0"
    assert store.uninstall("acme.tools").definition.plugin_id == "acme.tools"
    assert [event.action.value for event in store.audit()] == [
        "install",
        "enable",
        "disable",
        "update",
        "update",
        "delete",
    ]


def test_dependency_and_permission_validation_is_atomic() -> None:
    store = marketplace()
    store.register(
        definition(
            dependencies=(PluginDependency("missing", "1.0.0"),),
            permissions=frozenset({"secrets"}),
        )
    )
    with pytest.raises(PluginError, match="Denied"):
        store.install("acme.tools")
    assert store.registry.list() == ()
    assert store.metrics.snapshot()["plugin_failure_total"] == 1


def test_loader_validates_dependencies_and_runs_lifecycle(tmp_path: Path) -> None:
    (tmp_path / "plugin.py").write_text(
        "class Plugin:\n"
        "    def __init__(self): self.started = False\n"
        "    def initialize(self): self.started = True\n"
        "    def shutdown(self): self.started = False\n",
        encoding="utf-8",
    )
    loader = MarketplacePluginLoader()
    plugin = loader.load_definition(tmp_path, definition(), {})
    assert plugin.started
    loader.unload(plugin)
    assert not plugin.started
    with pytest.raises(PluginError, match="dependencies"):
        loader.validate(
            definition(dependencies=(PluginDependency("base", "1.0"),)),
            {},
        )


def test_sandbox_permissions_timeout_and_signing() -> None:
    policy = PermissionPolicy(frozenset({PluginPermission.NETWORK}))
    policy.validate(frozenset({"network"}))
    with pytest.raises(PluginError, match="Denied"):
        policy.validate(frozenset({"filesystem"}))
    sandbox = PluginSandbox(
        SandboxPolicy(permissions=policy, limits=ExecutionLimits(0.01, 1024))
    )
    assert sandbox.execute(lambda: 42) == 42
    with pytest.raises(PluginError, match="timed out"):
        sandbox.execute(lambda: time.sleep(0.05))
    payload = b"signed plugin"
    signer = PluginSigner(b"enterprise-key")
    signer.verify(payload, checksum(payload), signer.sign(payload))
    with pytest.raises(PluginError, match="checksum"):
        signer.verify(payload, "0" * 64, signer.sign(payload))


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self,
        path: str,
        _endpoint: object,
        methods: list[str],
        *,
        tags: list[str],
    ) -> None:
        assert tags == ["plugins"]
        self.routes.append((path, tuple(methods)))


def test_api_routes_and_operations() -> None:
    store = marketplace()
    store.register(definition(permissions=frozenset({"workflow", "agent"})))
    app = FakeApp()
    bridge = register_plugin_routes(app, store)
    assert app.routes == [
        ("/plugins", ("GET",)),
        ("/plugins/install", ("POST",)),
        ("/plugins/{plugin_id}", ("DELETE",)),
        ("/plugins/enable", ("POST",)),
        ("/plugins/disable", ("POST",)),
        ("/plugins/update", ("POST",)),
    ]
    assert bridge.list_plugins()["total"] == 1
    assert bridge.install({"id": "acme.tools"})["state"] == "installed"
    assert bridge.enable({"id": "acme.tools"})["state"] == "enabled"
    assert bridge.disable({"id": "acme.tools"})["state"] == "disabled"
    assert bridge.uninstall("acme.tools")["id"] == "acme.tools"


def test_dashboard_and_metrics_contracts() -> None:
    root = Path(__file__).parents[2]
    app = (root / "dashboard/frontend/src/App.tsx").read_text(encoding="utf-8")
    pages = (root / "dashboard/frontend/src/pages.tsx").read_text(encoding="utf-8")
    for route in ("plugins", "marketplace", "installed", "updates"):
        assert f'path="/{route}"' in app
    assert "PluginDetailsPage" in pages
    assert "PluginPermissionsPage" in pages
    metrics = marketplace().metrics.render_prometheus()
    for name in (
        "plugin_install_total",
        "plugin_load_total",
        "plugin_failure_total",
        "plugin_execution_seconds",
    ):
        assert name in metrics


def test_existing_registry_remains_independent() -> None:
    assert MarketplaceRegistry().list() == ()
    assert isinstance(PluginApi(marketplace()), PluginApi)
