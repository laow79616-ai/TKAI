# V8 Coordination Operations Guide

Use the GET-only `/v8/coordination/*` endpoints or the dashboard to inspect
profiles, frameworks, graphs, synchronization plans, compatibility,
governance, health, and metrics. Treat cycle diagnostics as review findings.

Operational checks:

1. Confirm health reports execution and runtime synchronization as disabled.
2. Review graph cycles and compatibility references.
3. Confirm tenant, workspace, and framework scope before exposing metadata.
4. Review secret-filtered audit records.
5. Route any action proposal to an existing separately authorized system.
