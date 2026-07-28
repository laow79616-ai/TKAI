# Upgrading to TKAI V5.0

1. Stop TKAI and verify no owned PID remains.
2. Create and validate a V4 backup.
3. Retain the previous checkout, configuration, and release archive.
4. Install V5 dependencies and rebuild both frontends.
5. Start V5. Database initialization is idempotent and checks integrity.
6. Verify `/health`, `/readiness`, `/tiktok/system/health`, Dashboard, and AI Studio.
7. Run the release checklist before normal operation.

Rollback by stopping V5, restoring the retained release and verified backup if
required, and re-running health checks.
