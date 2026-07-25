# AI Provider Framework

TKAI exposes provider-neutral `ChatMessage`, `ChatRequest`, `ChatResponse`,
embeddings, `ProviderManager`, capability routing, fallback policy, and
read-only diagnostics. `AIClient.generate()` remains available for existing
applications.

## Public call paths

`OpenAICompatibleProvider` exposes additive async methods `achat()`,
`astream_chat()`, and `aclose()`. Its existing `chat()`, `stream_chat()`, and
`close()` methods remain synchronous compatibility APIs. The sync bridge does
not nest an event loop: synchronous calls made inside an active loop raise a
clear configuration error and callers should use the async methods instead.

ProviderManager is the shared routing facade for `chat`, `achat`,
`stream_chat`, `astream_chat`, and `embed`. Explicit provider names and
aliases are honored; provider-prefixed models such as
`openrouter/anthropic/model` retain the complete model suffix.

## Capabilities and fallback

Use `Capability` enum values with `required_capabilities` to require chat,
streaming, embeddings, tools, vision, JSON mode, or async support. Provider
defaults can have exact per-model `ProviderCapabilities` overrides. An empty
capability request preserves default routing behavior.

`FallbackEngine` is independent of the manager. It consumes an already ordered
candidate list, retries only temporary errors within its budget, skips
blacklisted providers, and switches stream candidates only before the first
business chunk is emitted.

## Offline operation

`OpenAICompatibleProvider` supports injected legacy callables and
`AsyncTransport` implementations. `AsyncHTTPTransport` is available for
application-owned production wiring, while all framework tests use fakes or
mock transports and never contact provider endpoints.
