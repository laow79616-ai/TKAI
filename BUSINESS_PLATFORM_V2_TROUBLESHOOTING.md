# TKAI Business Platform V2 Troubleshooting

Run `scripts/status-all.ps1`, `scripts/health-check.ps1`, then
`scripts/collect-diagnostics.ps1`. If a port is occupied, set an alternate port in
`.env`; do not terminate the unrelated process. A 401 means the token is missing,
expired, invalid, or revoked. A missing record may indicate the wrong tenant/workspace.
A rejected payload commonly contains a secret value rather than an opaque reference.
Diagnostics are redacted, but review them before sharing.
