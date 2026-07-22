# AI Provider Framework

TKAI exposes provider-neutral `ChatMessage`, `ChatRequest`, `ChatResponse`,
embedding models, and `ProviderManager`. Existing `AIClient.generate()` stays
available for compatibility. Providers receive injected transports in tests,
so the framework never requires network access to import or test.

Use `OpenAICompatibleProvider` for OpenAI, DeepSeek, Qwen-compatible, and
custom compatible endpoints. `OpenRouterProvider` adds `HTTP-Referer` and
`X-Title` headers. API keys are hidden from dataclass representations.

Optional Anthropic and Gemini adapters perform lazy dependency validation and
raise clear configuration errors when their SDK is absent.
