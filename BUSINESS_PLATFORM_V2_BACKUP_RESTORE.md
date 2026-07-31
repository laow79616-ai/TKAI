# TKAI Business Platform V2 Backup and Restore

Create a local backup with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup-local.ps1
```

Verify the reported archive and checksum. Restore remains a non-destructive reference
workflow by default. Use `scripts/restore-local-reference.ps1` to inspect a candidate;
an authorized administrator must explicitly confirm a separately scheduled restore.
Never overwrite the active database silently.
