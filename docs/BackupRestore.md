# TKAI V5.0 Backup and Restore

`.\scripts\backup-tkai.ps1` creates a timestamped backup containing the SQLite
database, sanitized configuration, runtime metadata, and a SHA-256 manifest.
Retention is bounded by `backup_retention_count`.

```powershell
.\scripts\stop-tkai.ps1
.\scripts\restore-tkai.ps1 -Backup runtime\backups\<timestamp>
```

Restore verifies ownership and checksums, requires explicit confirmation,
creates a safety backup, preserves the active external secret reference, and
then replaces the database. Never copy or restore a live SQLite database.
