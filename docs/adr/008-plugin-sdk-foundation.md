# ADR 008: Plugin SDK Foundation

## Status

Accepted.

## Decision

Add immutable SDK metadata, a preferred initialize/shutdown interface, compatibility lifecycle dispatch for legacy plugins, thread-safe registration, stable hooks, and EventBus lifecycle events.

## Rationale

An explicit interface makes local extensions discoverable without altering provider APIs. Stable hook ordering makes behavior testable. Lifecycle compatibility preserves existing plugins. Failure isolation prevents a plugin hook from breaking the runtime caller.

## Consequences

Plugins are local Python objects only. There is no marketplace, remote installation, sandboxing, dependency resolution, hot reload, update mechanism, WebAssembly, or ProviderManager default takeover.
