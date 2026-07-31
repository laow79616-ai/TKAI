# Local Troubleshooting

Run `scripts/validate-environment.ps1`, `scripts/status-all.ps1`, and `scripts/health-check.ps1` in that order. Port-in-use errors must be resolved without terminating unrelated processes. Inspect `runtime/logs/*-error.log`; then collect diagnostics. If npm PowerShell execution is restricted, scripts use `npm.cmd`. Reinstall only the affected component with an `install-*.ps1` script.
