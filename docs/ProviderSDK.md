# TKAI 2.0 Provider SDK

## Architecture

`tkai.sdk.provider` is a vendor-neutral contract layer. It defines immutable
requests, responses, configuration, capabilities, lifecycle values, transport,
client, registry, factory, hooks, and middleware interfaces. It does not import
or modify V1.x provider implementations.

## Lifecycle and configuration

`ProviderConfiguration` is immutable and caller supplied: timeout, retry count,
headers, base URL, model, API version, and metadata are never discovered from
environment variables or credentials. Providers are constructed explicitly by
`ProviderFactory` and registered explicitly in `ProviderRegistry`.

## Streaming and middleware

`StreamingResponse` exposes a finite synchronous iterator plus `cancel()` and
`close()`. `AsyncStreamingResponse` is a reserved interface only. No threads,
network I/O, or unbounded buffering is introduced. `MiddlewarePipeline` defines
ordered before-request, after-response, and error boundaries for future Retry,
Telemetry, Logging, and Metrics hooks.

## Capabilities

The extensible `ProviderCapability` enum includes chat, completion, embeddings,
image, audio, tool/function calling, streaming, JSON mode, structured output,
and vision. Registry capability checks use declarations, not vendor names.

## Reference Provider

`ReferenceProvider` is an offline deterministic implementation for tests,
documentation, factories, and SDK smoke checks. It is not an OpenAI, Anthropic,
Gemini, or other production provider and never contacts a network service.

## Current limitations

Real provider adapters, async execution, transport implementations, persistent
configuration, and production retry/telemetry integrations are intentionally
deferred to later sprints.
