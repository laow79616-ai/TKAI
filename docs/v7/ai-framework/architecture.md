# V7 Unified AI Framework Architecture

The framework is a bounded metadata plane for providers, models, templates,
reasoning sessions, evaluation, governance, safety, observability, and audit.
It stores no chain-of-thought and exposes no provider invocation or TikTok
action surface. Every record is tenant/workspace scoped.

Routing is deterministic metadata selection: active models must match requested
capabilities, modalities, compatible versions, and approved governance records.
The returned decision is explicitly non-executable and includes fallback IDs.
