# AI Studio Architecture

The Studio domain is provider-neutral and uses immutable models. Project,
prompt, chat, knowledge, RAG, model, evaluation, and workflow services expose
small typed interfaces. FastAPI and React are adapters. Metrics use stable names
and can be bridged to the existing Prometheus/OpenTelemetry stack.

Dependency direction is `dashboard/API -> Studio services -> interface`, with
runtime, provider, storage, and retrieval implementations injected from the
preserved SDK, Cloud Native, Enterprise Platform, and Plugin Marketplace layers.
