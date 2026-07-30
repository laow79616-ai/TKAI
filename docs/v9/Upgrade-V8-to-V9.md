# Upgrade from V8 to V9

1. Back up configuration and storage using the established V8 procedures.
2. Confirm Python 3.10+ and frontend build prerequisites.
3. Validate the V9 archive and SHA-256 manifest.
4. Deploy using the unchanged V8 deployment workflow.
5. Verify V6-V9 API availability, health, dashboards, AI Studio, and TikTok
   regressions.

No automatic migration or upgrade runs. V9 adds advisory APIs and does not
alter V8 schemas or business behavior. If validation fails, redeploy V8 using
the established deployment process.
