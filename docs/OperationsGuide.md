# TKAI Platform Operations Guide

## Deploy

Deploy the pinned `tkai` distribution into a Python 3.10+ environment, verify
the package version, then run the offline Doctor checks. Studio hosts must
explicitly supply FastAPI/Uvicorn and their SDK Gateway; importing Studio never
starts a server.

For frontend delivery, build the packaged Studio React source in the target
Node environment. Keep frontend assets and backend deployment configuration
under the host's normal release controls.

## Backup and recovery

Platform reference stores are local memory. There is no built-in persistent
Studio backup, database migration, or distributed state synchronization. If a
host adds persistence, its backup and retention procedures are host-owned and
must be tested separately.

## Upgrade

1. Read the target release notes and compatibility notes.
2. Create a reproducible environment with the target package version.
3. Run `tkai version show`, `tkai doctor`, and applicable offline integration
   tests before switching traffic.
4. Rebuild Studio frontend assets in the target Node toolchain when used.

## Rollback

Roll back by restoring the previously pinned package and host configuration.
Because Platform 1.0 introduces no automatic migrations or persisted Studio
state, rollback does not include a TKAI-managed data migration. Validate the
previous environment with the same Doctor and smoke checks before resuming use.
