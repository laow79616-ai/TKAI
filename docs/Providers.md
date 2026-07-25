# Provider Development Guide

Provider configuration uses `ProviderConfig(name, type, api_key, base_url,
model, timeout, max_retries, headers)`. Keep credentials in application
configuration and never render raw configuration or headers in logs. The
dataclass excludes API keys from its representation.

## Implementing a provider

Implement `AIProvider.generate()` for legacy `AIClient` compatibility. A
provider that supports normalized requests should also implement `chat()` and
optionally `stream_chat()`, `achat()`, and `astream_chat()`. Declare a
`ProviderCapabilities` instance; unknown capabilities are not assumed.

Register a cached instance with `ProviderManager.register()`. Optional aliases,
provider-level capabilities, and exact model-level capability overrides are
also declared at registration. The manager owns selection and lifecycle, so
applications should not duplicate provider collections.

```python
manager.register(
    provider,
    default=True,
    aliases=("primary",),
    capabilities=ProviderCapabilities(chat=True, tools=True),
    model_capabilities={"vision-model": ProviderCapabilities(chat=True, vision=True)},
)
```

## OpenAI-compatible providers

`OpenAICompatibleProvider` is shared by OpenAI, DeepSeek, Qwen, OpenRouter,
and compatible endpoints. Prefer an injected `AsyncTransport`; a legacy
callable is adapted through `TransportAdapter`. Providers must not expose SDK
objects in `ChatResponse` or leak authorization headers in errors.

## Verification

Provider tests must inject transports or SDK fakes. Cover sync, async,
streaming, close ownership, normalized errors, and capability declarations;
do not invoke real provider endpoints in tests.
