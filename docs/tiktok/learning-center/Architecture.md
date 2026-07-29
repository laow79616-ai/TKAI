# TikTok Autonomous Learning Center Architecture

The Learning Center is a tenant- and workspace-scoped, read-only knowledge
improvement layer. It consumes immutable historical snapshots through bounded
adapters, performs deterministic offline analysis, and emits explainable
patterns, lessons, evaluations, analytics, and advisory recommendations.

Its adapters deliberately expose only `read_history`. They have no runtime
configuration, execution, publishing, credential, browser, device, proxy, or
restriction-bypass operation. Existing TikTok services remain the systems of
record; this center does not duplicate their infrastructure.

All records carry evidence references and confidence. API routes are GET-only.
Creation and analysis methods are internal offline workflows protected by RBAC,
tenant isolation, workspace isolation, safe-record validation, and audit events.
