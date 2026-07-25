# Plugin Framework

Plugins live in a root directory such as `plugins/<name>/` and require a
`plugin.json` manifest containing `name`, `version`, and `entry`.

```json
{"name": "example", "version": "1.0.0", "entry": "plugin:ExamplePlugin"}
```

The entry class implements `activate(context)` and `deactivate(context)`.
`PluginDiscovery` reads manifests, `PluginLoader` resolves local entries,
`PluginRegistry` owns instances, and `PluginManager` coordinates lifecycle.
`PluginManager.discover()` and `load_all()` use the repository `plugins/`
directory by default.
