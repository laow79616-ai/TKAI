# V7 Operations Guide

V7 is disabled unless application code constructs a kernel. Use structured JSON
logging with `filter_secrets`, register health checks by unique name, and connect
metrics, tracing, and audit hooks to deployment-owned backends.

Safe defaults disable automatic migration and extension loading and use
deny-by-default authorization. Validate configuration before module
registration. Stop the kernel during graceful shutdown and treat lifecycle
failures as unhealthy.

Deployment readiness checks include Ruff, configured mypy, full pytest, targeted
TikTok/deployment/release/local-runtime suites, both frontend production builds,
OpenAPI and PowerShell contract tests, and `git diff --check`.
