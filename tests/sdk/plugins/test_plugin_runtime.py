"""Local lifecycle, dependency, hook, loader, and reference-plugin coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from tkai.sdk.memory import MemoryRecord, ReferenceMemory
from tkai.sdk.plugins.runtime import (
    EchoPlugin,
    MemoryPlugin,
    PluginContext,
    PluginDependency,
    PluginDependencyError,
    PluginLifecycle,
    PluginLoader,
    PluginManifest,
    PluginRegistry,
    PluginRuntime,
    WorkflowPlugin,
)
from tkai.sdk.workflow import Node, WorkflowDefinition, WorkflowRuntime


def test_lifecycle_loader_registry_hooks_and_echo_plugin_are_explicit() -> None:
    """Loading through enable and unload uses only supplied local plugin objects."""
    events: list[str] = []

    class Hook:
        def before_load(self, manifest: PluginManifest) -> None:
            events.append(f"before:{manifest.name}")

        def after_load(self, manifest: PluginManifest) -> None:
            events.append(f"after:{manifest.name}")

        def before_execute(self, manifest: PluginManifest) -> None:
            events.append(f"execute:{manifest.name}")

        def after_execute(self, manifest: PluginManifest) -> None:
            events.append(f"done:{manifest.name}")

        def on_error(self, manifest: PluginManifest | None, error: Exception) -> None:
            del manifest, error

    registry = PluginRegistry()
    runtime = PluginRuntime(registry, (Hook(),))
    plugin = EchoPlugin()
    assert runtime.load(plugin) is PluginLifecycle.LOADED
    assert (
        runtime.initialize(plugin.manifest.name, PluginContext())
        is PluginLifecycle.INITIALIZED
    )
    assert runtime.enable(plugin.manifest.name) is PluginLifecycle.ENABLED
    assert runtime.execute(plugin.manifest.name, "echo") == "echo"
    assert runtime.disable(plugin.manifest.name) is PluginLifecycle.DISABLED
    assert runtime.unload(plugin.manifest.name) is PluginLifecycle.UNLOADED
    assert events == [
        "before:echo-plugin",
        "after:echo-plugin",
        "execute:echo-plugin",
        "done:echo-plugin",
    ]

    loader = PluginLoader(registry)
    loaded = loader.load(EchoPlugin("loaded"))
    assert registry.lookup("loaded") is loaded


def test_dependency_resolution_detects_missing_and_cyclic_local_graphs() -> None:
    """Dependency sorting is deterministic and does not attempt remote downloads."""
    registry = PluginRegistry()
    base = EchoPlugin("base")
    dependent = EchoPlugin("dependent")
    dependent.manifest = PluginManifest(
        "dependent", dependencies=(PluginDependency("base"),)
    )
    registry.register(base)
    registry.register(dependent)
    assert [item.manifest.name for item in registry.resolve("dependent")] == [
        "base",
        "dependent",
    ]

    missing = EchoPlugin("missing")
    missing.manifest = PluginManifest(
        "missing", dependencies=(PluginDependency("absent"),)
    )
    registry.register(missing)
    with pytest.raises(PluginDependencyError):
        registry.resolve("missing")

    first = EchoPlugin("first")
    second = EchoPlugin("second")
    first.manifest = PluginManifest("first", dependencies=(PluginDependency("second"),))
    second.manifest = PluginManifest(
        "second", dependencies=(PluginDependency("first"),)
    )
    cyclic = PluginRegistry()
    cyclic.register(first)
    cyclic.register(second)
    with pytest.raises(PluginDependencyError):
        cyclic.resolve("first")


def test_memory_and_workflow_reference_plugins_use_explicit_dependencies() -> None:
    """Reference plugins compose existing SDK objects without creating replacements."""
    memory = ReferenceMemory()
    memory.store(MemoryRecord("key", "value"))
    runtime = PluginRuntime()
    memory_plugin = MemoryPlugin()
    runtime.load(memory_plugin)
    runtime.initialize(memory_plugin.manifest.name, PluginContext(memory=memory))
    runtime.enable(memory_plugin.manifest.name)
    assert runtime.execute(memory_plugin.manifest.name, "key") == "value"

    workflow = WorkflowRuntime(
        WorkflowDefinition("flow", (Node("task", handler="done"),), "task")
    )
    workflow_plugin = WorkflowPlugin()
    runtime.load(workflow_plugin)
    runtime.initialize(workflow_plugin.manifest.name, PluginContext(workflow=workflow))
    runtime.enable(workflow_plugin.manifest.name)
    assert runtime.execute(workflow_plugin.manifest.name).output == "done"


def test_registry_thread_safety_uses_stable_local_snapshots() -> None:
    """Concurrent local registration remains deterministic without dynamic loading."""
    registry = PluginRegistry()
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda index: registry.register(EchoPlugin(f"plugin-{index}")),
                range(32),
            )
        )
    assert [plugin.manifest.name for plugin in registry.list()] == sorted(
        f"plugin-{index}" for index in range(32)
    )
