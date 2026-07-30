# Hyper Reasoning Operations Guide

Use `health()` for mode, isolation boundary, source counts, and diagnostics.
Use `metrics()` for registry counts, aggregated reference counts, and
observability counters. Structured logs, trace hooks, and audit records are
available in `snapshot()`.

The public API exposes only:

- `/v8/reasoning/profiles`
- `/v8/reasoning/evidence`
- `/v8/reasoning/knowledge`
- `/v8/reasoning/confidence`
- `/v8/reasoning/recommendations`
- `/v8/reasoning/explanations`
- `/v8/reasoning/compatibility`
- `/v8/reasoning/health`
- `/v8/reasoning/metrics`

Every route is GET-only. Investigate unresolved evidence diagnostics, reduced
coverage, or isolation failures without enabling runtime adapters; the fabric
has no action execution path.
