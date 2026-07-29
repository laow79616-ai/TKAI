# Knowledge Evolution Operations Guide

Use the shared API process and inspect `/tiktok/knowledge/dashboard`,
`/tiktok/knowledge/analytics`, and `/tiktok/knowledge/metrics`. The required
Prometheus gauges cover profiles, versions, recommendations, confidence, and
refinement latency.

Audit records contain actor, tenant, workspace, action, and resource identifiers.
Do not place secrets in profile metadata; secret-like keys are rejected and no
knowledge payload is written to logs.

For incidents, verify source availability and scope, review the evolution
timeline, and retry the read. There is no executor, publisher, background worker,
or runtime configuration to recover.
