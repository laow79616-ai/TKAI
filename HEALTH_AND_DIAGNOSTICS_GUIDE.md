# Health and Diagnostics

Run `scripts/health-check.ps1` for liveness/readiness and UI probes, `scripts/smoke-test.ps1` for offline acceptance, and `scripts/collect-diagnostics.ps1` for a sanitized bundle. Logs are in `runtime/logs`; exports are in `runtime/exports`. Diagnostic output redacts passwords, keys, cookies, sessions, authorization values, and proxy credentials.
