# AI Provider Migration Guide

## Existing applications

No migration is required for existing `AIClient.generate()`, `AIProvider`,
`ProviderManager.register/get/names/chat/embed/close`, or synchronous
`OpenAICompatibleProvider.chat/stream_chat/close` callers. Existing command
names under `tkai ai` are retained as compatibility commands.

## Additive APIs

New code may use `ChatRequest`/`ChatResponse`, `ProviderManager.achat()`,
`ProviderManager.astream_chat()`, `Capability`, `FallbackEngine`, and
`DoctorService`. These additions do not require replacing an injected legacy
callable: `TransportAdapter` provides the compatibility boundary.

## Async migration

Use `await provider.achat(request)` or `await manager.achat(request)` inside
FastAPI, notebooks, or any running event loop. Do not call synchronous
`chat()` from an active event loop; the SyncBridge rejects nested execution
with a clear error.

## Capability migration

Empty `required_capabilities` preserves prior default routing. Introduce
capabilities gradually by declaring `ProviderCapabilities` at registration and
passing typed `Capability` enum members only where a feature is required.

## Fallback migration

Fallback is intentionally separate from routing. Pass the stable,
capability-filtered candidate list to `FallbackEngine`; do not add retry or
failover rules to individual providers.
