# Operator Runbook

Use `scripts/status-all.ps1`, `scripts/health-check.ps1`, `scripts/restart-all.ps1`, and `scripts/stop-all.ps1` for daily operation. Create a backup with `scripts/backup-local.ps1`; collect redacted diagnostics with `scripts/collect-diagnostics.ps1`. Logs are under `runtime/logs`. Scripts control only processes recorded in checkout-owned PID files.
