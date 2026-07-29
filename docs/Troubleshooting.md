# TKAI V6.0 Troubleshooting

Run `scripts/diagnose-tkai.ps1` and `scripts/health-tkai.ps1` first. A failed
frontend build normally indicates an out-of-date lockfile or unsupported Node
runtime; use `npm ci` and rebuild. A release validation failure should be
resolved at its named gate rather than bypassed.

Repository-wide mypy can stop when it discovers duplicate packaged modules
under `artifacts/`. Those generated copies are a known repository artifact
issue; remove or exclude generated artifacts for analysis and continue the
remaining release gates. Treat duplicate imports outside `artifacts/` as a
release blocker.

Never paste secrets into diagnostics. Logs and reports should contain only
redacted references. A failed health, RBAC, isolation, OpenAPI, checksum, or
secret-scan gate blocks release.

- Missing configuration: copy `configuration/local.example.json`.
- Port conflict: stop the owning process or choose three unique loopback ports.
- Stale PID: `stop-tkai.ps1` removes a scoped stale reference without killing an unrelated process.
- Partial startup: reverse-order rollback runs; inspect `runtime/logs/*-error.log`.
- Database failure: stop services, validate a backup manifest, then restore.
- Dashboard or Studio unavailable: run its production build and inspect its log.
- Not-ready module: inspect `/tiktok/system/health` for modules and duplicate routes.

Collect sanitized diagnostics with `.\scripts\diagnose-tkai.ps1`.
