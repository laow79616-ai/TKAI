# Plugin SDK Foundation

TKAI Plugin SDK is an optional, local Python extension mechanism. Existing legacy plugins using `activate(context)` and `deactivate(context)` remain supported. New SDK plugins use `initialize()` and `shutdown()` with immutable `PluginMetadata`.

`PluginManager` owns a thread-safe registry, lifecycle calls, enabled state, and failure-isolated hook dispatch. Hook names cover request, routing, health, cache, rate-limit, and provider events. Enabled plugins run in priority-descending then name order. Hook errors emit `PluginFailed` and do not interrupt the caller.

Plugin lifecycle events (`PluginLoaded`, `PluginUnloaded`, `PluginEnabled`, `PluginDisabled`, and `PluginFailed`) reuse the shared Observability EventBus. No plugin is loaded by default, and the SDK does not change Runtime or ProviderManager behavior.

```console
tkai ai plugins
tkai ai plugins --json
```

Doctor reports loaded, enabled, disabled, failed plugins, and hook count without invoking plugins. Current limitations: local Python plugins only; no marketplace, remote loading, sandboxing, hot reload, dependency resolver, automatic updates, or WebAssembly.
