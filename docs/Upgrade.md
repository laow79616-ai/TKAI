# Upgrading to TKAI V6.0

V6.0 preserves the V5 functional scope and public execution boundaries.
Upgrade by backing up runtime data, recording the current configuration and
artifact checksum, installing the 6.0.0 package, rebuilding the Dashboard and
AI Studio, and running database initialization plus health and OpenAPI checks.

Compare configuration with `configuration/local.example.json`; keep secrets in
the environment or approved secret store. Do not copy `.env`, runtime
databases, cookies, sessions, credentials, logs, or caches into the release
archive.

Rollback by stopping V6, restoring the prior package and configuration, and
using the verified backup through `scripts/restore-tkai.ps1`. Validate health,
tenant/workspace isolation, and audit continuity before resuming service.

1. Stop the existing TKAI deployment and verify no owned PID remains.
2. Create and validate a backup with the currently deployed release.
3. Retain the previous checkout, configuration, release archive, and checksums.
4. Install V6 dependencies and rebuild both frontends.
5. Start V6. Database initialization remains idempotent and validates integrity.
6. Verify `/health`, `/readiness`, `/tiktok/system/health`, `/openapi.json`,
   Dashboard, and AI Studio.
7. Run the V6 release checklist before restoring normal traffic.
