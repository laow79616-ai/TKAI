"""Explicit local Plugin Runtime and deterministic reference plugin objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Protocol

from .errors import PluginLifecycleError
from .hooks import PluginHook
from .lifecycle import PluginLifecycle
from .manifest import PluginManifest
from .registry import PluginRegistry


@dataclass(slots=True)
class PluginContext:
    """Explicit SDK dependencies available to a local plugin lifecycle call."""

    tools: object | None = None
    workflow: object | None = None
    memory: object | None = None
    provider: object | None = None
    agent: object | None = None
    metadata: dict[str, object] = field(default_factory=dict)


class Plugin(Protocol):
    """Local plugin contract; no loading or lifecycle method is invoked implicitly."""

    @property
    def manifest(self) -> PluginManifest: ...

    def initialize(self, context: PluginContext) -> None: ...

    def enable(self) -> None: ...

    def disable(self) -> None: ...

    def shutdown(self) -> None: ...


class PluginRuntime:
    """Coordinate only explicit local plugin lifecycle actions and dependencies."""

    def __init__(
        self, registry: PluginRegistry | None = None, hooks: tuple[PluginHook, ...] = ()
    ) -> None:
        self.registry = registry or PluginRegistry()
        self._hooks = hooks
        self._states: dict[str, PluginLifecycle] = {}
        self._lock = RLock()

    def load(self, plugin: Plugin) -> PluginLifecycle:
        """Register one supplied local plugin in the loaded state."""
        with self._lock:
            self._notify("before_load", plugin.manifest)
            self.registry.register(plugin)
            self._states[plugin.manifest.name] = PluginLifecycle.LOADED
            self._notify("after_load", plugin.manifest)
            return PluginLifecycle.LOADED

    def initialize(self, name: str, context: PluginContext) -> PluginLifecycle:
        """Initialize one loaded plugin with caller-supplied SDK dependencies."""
        with self._lock:
            plugin = self.registry.lookup(name)
            self._require_state(name, PluginLifecycle.LOADED, PluginLifecycle.DISABLED)
            try:
                plugin.initialize(context)
            except Exception as error:
                self._on_error(plugin.manifest, error)
                raise
            self._states[name] = PluginLifecycle.INITIALIZED
            return PluginLifecycle.INITIALIZED

    def enable(self, name: str) -> PluginLifecycle:
        """Enable an initialized local plugin explicitly."""
        with self._lock:
            plugin = self.registry.lookup(name)
            self._require_state(
                name, PluginLifecycle.INITIALIZED, PluginLifecycle.DISABLED
            )
            plugin.enable()
            self._states[name] = PluginLifecycle.ENABLED
            return PluginLifecycle.ENABLED

    def disable(self, name: str) -> PluginLifecycle:
        """Disable one enabled local plugin explicitly."""
        with self._lock:
            plugin = self.registry.lookup(name)
            self._require_state(name, PluginLifecycle.ENABLED)
            plugin.disable()
            self._states[name] = PluginLifecycle.DISABLED
            return PluginLifecycle.DISABLED

    def unload(self, name: str) -> PluginLifecycle:
        """Disable if needed and unregister one plugin without remote side effects."""
        with self._lock:
            if self._states.get(name) is PluginLifecycle.ENABLED:
                self.disable(name)
            plugin = self.registry.unregister(name)
            plugin.shutdown()
            self._states[name] = PluginLifecycle.UNLOADED
            return PluginLifecycle.UNLOADED

    def reload(self, name: str) -> PluginLifecycle:
        """Reload the same local object; dynamic module reload remains out of scope."""
        with self._lock:
            plugin = self.registry.lookup(name)
            self.unload(name)
            return self.load(plugin)

    def shutdown(self) -> None:
        """Explicitly unload all registered plugins in reverse stable order."""
        for plugin in reversed(self.registry.list()):
            self.unload(plugin.manifest.name)

    def state(self, name: str) -> PluginLifecycle:
        """Return the observed runtime state for one registered or unloaded plugin."""
        with self._lock:
            if name not in self._states:
                raise PluginLifecycleError(f"Plugin state unavailable: {name}")
            return self._states[name]

    def resolve(self, name: str) -> tuple[Plugin, ...]:
        """Resolve local dependency-first loading order through the registry."""
        return self.registry.resolve(name)

    def execute(self, name: str, *arguments: object, **keywords: object) -> object:
        """Invoke an enabled reference plugin's explicit local execute method."""
        with self._lock:
            plugin = self.registry.lookup(name)
            self._require_state(name, PluginLifecycle.ENABLED)
            execute = getattr(plugin, "execute", None)
            if not callable(execute):
                raise PluginLifecycleError(
                    f"Plugin {name} has no executable interface."
                )
            self._notify("before_execute", plugin.manifest)
            try:
                result = execute(*arguments, **keywords)
            except Exception as error:
                self._on_error(plugin.manifest, error)
                raise
            self._notify("after_execute", plugin.manifest)
            return result

    def _require_state(self, name: str, *allowed: PluginLifecycle) -> None:
        state = self._states.get(name)
        if state not in allowed:
            names = ", ".join(item.value for item in allowed)
            raise PluginLifecycleError(f"Plugin {name} must be in: {names}")

    def _notify(self, method: str, manifest: PluginManifest) -> None:
        for hook in self._hooks:
            try:
                getattr(hook, method)(manifest)
            except Exception:
                continue

    def _on_error(self, manifest: PluginManifest, error: Exception) -> None:
        for hook in self._hooks:
            try:
                hook.on_error(manifest, error)
            except Exception:
                continue


@dataclass(slots=True)
class _ReferencePlugin:
    """Shared lifecycle mechanics for local-only reference plugins."""

    manifest: PluginManifest
    initialized: bool = field(default=False, init=False)
    enabled: bool = field(default=False, init=False)
    context: PluginContext | None = field(default=None, init=False, repr=False)

    def initialize(self, context: PluginContext) -> None:
        """Store only explicitly supplied in-process context."""
        self.context = context
        self.initialized = True

    def enable(self) -> None:
        """Enable this reference plugin after explicit initialization."""
        if not self.initialized:
            raise PluginLifecycleError("Reference plugin must be initialized first.")
        self.enabled = True

    def disable(self) -> None:
        """Disable idempotently without external cleanup work."""
        self.enabled = False

    def shutdown(self) -> None:
        """Clear local context and disable the reference plugin idempotently."""
        self.enabled = False
        self.context = None


class EchoPlugin(_ReferencePlugin):
    """Reference plugin returning supplied payloads without any network access."""

    def __init__(self, name: str = "echo-plugin") -> None:
        super().__init__(PluginManifest(name, capabilities=frozenset({"echo"})))

    def execute(self, value: object) -> object:
        """Return a local input unchanged when explicitly enabled."""
        if not self.enabled:
            raise PluginLifecycleError("Reference plugin is not enabled.")
        return value


class MemoryPlugin(_ReferencePlugin):
    """Reference plugin reading explicit compatible in-process memory."""

    def __init__(self, name: str = "memory-plugin") -> None:
        super().__init__(PluginManifest(name, capabilities=frozenset({"memory"})))

    def execute(self, key: str) -> object | None:
        """Read a value from explicitly injected compatible local memory."""
        if not self.enabled or self.context is None or self.context.memory is None:
            raise PluginLifecycleError(
                "Memory plugin requires enabled explicit memory."
            )
        get = getattr(self.context.memory, "get", None)
        if not callable(get):
            raise PluginLifecycleError("Memory plugin requires compatible memory.")
        record = get(key)
        return record.value if record is not None else None


class WorkflowPlugin(_ReferencePlugin):
    """Reference plugin invoking only an explicitly supplied workflow runtime."""

    def __init__(self, name: str = "workflow-plugin") -> None:
        super().__init__(PluginManifest(name, capabilities=frozenset({"workflow"})))

    def execute(self) -> object:
        """Invoke explicit workflow ``execute`` without constructing a runtime."""
        if not self.enabled or self.context is None or self.context.workflow is None:
            raise PluginLifecycleError(
                "Workflow plugin requires enabled explicit workflow."
            )
        execute = getattr(self.context.workflow, "execute", None)
        if not callable(execute):
            raise PluginLifecycleError("Workflow plugin requires compatible workflow.")
        return execute()
