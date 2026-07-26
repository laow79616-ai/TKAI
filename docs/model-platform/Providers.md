# Providers

Supported configuration types are OpenAI, Anthropic, Gemini, Azure OpenAI,
Ollama, local, and custom. `Provider`, `LocalProvider`, and `CustomProvider`
protocols keep integrations replaceable. Configurations contain only an opaque
credential reference; secrets belong in the deployment secret manager and must
not be logged.
