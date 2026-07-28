# TKAI V5.0 Troubleshooting

- Missing configuration: copy `configuration/local.example.json`.
- Port conflict: stop the owning process or choose three unique loopback ports.
- Stale PID: `stop-tkai.ps1` removes a scoped stale reference without killing an unrelated process.
- Partial startup: reverse-order rollback runs; inspect `runtime/logs/*-error.log`.
- Database failure: stop services, validate a backup manifest, then restore.
- Dashboard or Studio unavailable: run its production build and inspect its log.
- Not-ready module: inspect `/tiktok/system/health` for modules and duplicate routes.

Collect sanitized diagnostics with `.\scripts\diagnose-tkai.ps1`.
