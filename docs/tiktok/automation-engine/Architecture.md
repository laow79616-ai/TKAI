# TikTok AI Automation Engine

The Automation Engine is the bounded coordination layer for the single-user
local TikTok Cloud Control Platform. It owns automation definitions, reusable
plans, triggers, conditions, approvals, execution state, queues, monitoring,
recovery policy, and analytics. It calls the existing Workflow Center, Runtime
Manager, Scheduler, Resource Center, browser/device/account/proxy centers,
operations, risk, publishing, collection, interaction, analytics, and local
runtime through narrow ports. It does not copy their records or infrastructure.

The engine never performs CAPTCHA handling, restriction circumvention,
anti-detection, security bypass, spam, or unbounded mass action. A module health
response containing an unresolved TikTok restriction or challenge moves an
execution to `blocked`; retries and recovery stop until an operator resolves it.

All records carry tenant and workspace scope even though V5.0 remains a
single-user local deployment. RBAC is checked at service boundaries, approvals
are mandatory by default, metadata rejects secret-bearing keys, and adapters
must exchange encrypted references rather than plaintext credentials. Audit
events record lifecycle and execution changes without payload secrets.

API resources are rooted at `/tiktok/automation`; the dashboard consumes the
read-only dashboard projection. Prometheus metrics reuse the server's existing
metrics transport. The default port is deterministic and offline-only for local
tests; deployment code injects adapters to established modules.
