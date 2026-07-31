# Backup and Recovery

Run `scripts/backup-local.ps1` for a timestamped backup with manifest and SHA-256 checksums. Review its manifest before recovery. Restore is never automatic: run `scripts/restore-local-reference.ps1 -Backup <path> -ConfirmReplace` only after stopping services and independently preserving current data. Secret, cookie, session, and proxy credential material is excluded.
