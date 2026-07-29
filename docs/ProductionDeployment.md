# TKAI V7.0 Production Deployment Notes

Deploy only the validated `tkai-7.0.0.zip` artifact. Verify its adjacent
`.sha256` file, then verify the packaged `SHA256SUMS`. V7 remains opt-in;
existing V6 and TikTok processes may be deployed unchanged. Only documented
read-only health, diagnostics, metadata, and dashboard projections may be
routed from V7.

Deploy only the verified `v6.0.0` assets and compare their SHA-256 checksums
with the supplied integrity manifests. Keep credentials, sessions, cookies,
runtime databases, logs, and local `.env` files outside release packages.

Before deployment:

1. Record the current version, configuration, database state, and rollback owner.
2. Create and verify a restorable backup.
3. Install the optional dependencies required by the selected production profile.
4. Build the Dashboard and AI Studio and complete the V6 release checklist.

Before admitting traffic, verify database initialization, `/health`,
`/readiness`, `/metrics`, `/openapi.json`, `/tiktok/system/health`, Dashboard,
AI Studio, RBAC, tenant/workspace isolation, TLS, audit continuity, and log
redaction.

Rollback if initialization, integrity, health, isolation, or audit checks fail.
Stop V6, restore the retained prior package and configuration, restore the
verified backup if required, and repeat health checks before resuming traffic.
