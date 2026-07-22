# Plugin SDK migration note

Plugin SDK is an optional V1.1 addition. Existing V1 public APIs are unchanged, legacy `activate/deactivate` plugins remain compatible, and no plugin loads automatically. New plugins may use `PluginMetadata` with `initialize/shutdown` and explicit `PluginManager` registration.
