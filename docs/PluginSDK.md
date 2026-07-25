# TKAI 2.0 Plugin Runtime

## Architecture

`tkai.sdk.plugins.runtime` is an additive, reference-only composition layer for
explicit plugin objects. The pre-existing `tkai.sdk.plugins` extension
decorators remain compatible and independent. The runtime does not dynamically
import modules, contact a marketplace, or change the V1.x plugin system.

## Lifecycle and registry

`PluginRuntime` requires explicit `load`, `initialize`, `enable`, `disable`,
`unload`, `reload`, and `shutdown` calls. `PluginRegistry` is thread-safe and
supports register, unregister, lookup, list, and dependency-first resolution.
`PluginLoader` only accepts already constructed local plugin objects.

## Manifest and dependencies

`PluginManifest` includes name, version, author, description, dependencies,
capabilities, entry point metadata, and safe metadata. Resolution detects
missing and cyclic dependencies and produces stable local loading order. It
never downloads a dependency or interprets entry points.

## Hooks and reference plugins

Before/after load, before/after execute, error, and telemetry hook contracts
are available for caller-supplied observers; observer failures are isolated.
`EchoPlugin`, `MemoryPlugin`, and `WorkflowPlugin` are deterministic local
examples. Memory and workflow dependencies must be injected through
`PluginContext`.

## Current limitations

There is no marketplace, remote plugin, hot module reload, sandbox, MCP
runtime, Web UI, Studio, Enterprise integration, dependency download, or
automatic plugin discovery. Reference plugins are not production extensions.
