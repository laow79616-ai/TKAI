# Upgrading from TKAI V6.0 to V7.0

1. Back up configuration and persistent storage with the existing V6 tools.
2. Verify the V7 archive checksum and review `RELEASE_NOTES_V7.md`.
3. Deploy with the existing V6 configuration unchanged.
4. Run V6 health, TikTok, Dashboard, and AI Studio smoke checks.
5. Opt into V7 frameworks individually after their scoped validation.

No automatic data migration is performed. Roll back by restoring the V6
package and configuration backup; V7 metadata does not rewrite V6 data.

V6.0 preserves the V5 functional scope and public execution boundaries.
For V6-to-V7 upgrade, back up runtime data, record the current configuration
and artifact checksum, install the 7.0.0 package, rebuild the Dashboard and
AI Studio, and run health and OpenAPI checks. Database schema changes remain
operator-controlled; the release exposes no automatic migration endpoint.

Compare configuration with `configuration/local.example.json`; keep secrets in
the environment or approved secret store. Do not copy `.env`, runtime
databases, cookies, sessions, credentials, logs, or caches into the release
archive.

Rollback by stopping V6, restoring the prior package and configuration, and
using the verified backup through `scripts/restore-tkai.ps1`. Validate health,
tenant/workspace isolation, and audit continuity before resuming service.

1. Stop the existing TKAI deployment and verify no owned PID remains.
2. Create and validate a backup with the currently deployed V6 release.
3. Retain the V6 checkout, configuration, release archive, and checksums.
4. Install V7 dependencies and rebuild both frontends.
5. Start V7 with the existing configuration and V7 frameworks disabled.
6. Verify `/health`, `/readiness`, `/tiktok/system/health`, `/openapi.json`,
   Dashboard, AI Studio, isolation, redaction, and audit correlation.
7. Opt into V7 frameworks only after their scoped validation.
