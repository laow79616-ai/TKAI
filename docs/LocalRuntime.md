# TikTok Local Deployment & Runtime Center

## Quick start on Windows

Open PowerShell:

```powershell
Set-Location C:\Users\laow7\Documents\TKAI
Copy-Item configuration\local.example.json configuration\local.json
.\scripts\setup-tkai.ps1
.\scripts\start-tkai.ps1
```

Setup validates Python 3.10+, Node.js, and npm; creates `.venv`; installs Python
and frontend dependencies; installs Playwright Chromium; initializes the
configuration, runtime directories, and SQLite database; then builds Dashboard
and AI Studio. It never installs system-wide software.

Local URLs are API `http://127.0.0.1:8000`, Dashboard
`http://127.0.0.1:4173`, and AI Studio `http://127.0.0.1:4174`.

## Start, stop, status, and health

```powershell
.\scripts\start-tkai.ps1
.\scripts\status-tkai.ps1
.\scripts\health-tkai.ps1
.\scripts\stop-tkai.ps1
```

PID references include the repository path and command. Shutdown validates both
before stopping a process, cleans stale references, and preserves data and logs.
Startup fails on port conflicts or an early service exit.

## Configuration and security

Edit `configuration\local.json`. The supported modes are `development` and
`production-local`. All hosts default to loopback. Native local mode rejects
public/LAN bindings, paths outside the repository, duplicate or privileged ports,
and embedded database passwords. Use a secret-manager reference; never put a
secret in this file.

Runtime files are limited to:

- `runtime\data`
- `runtime\logs`
- `runtime\pids`
- `runtime\browser_profiles`
- `runtime\media`
- `runtime\exports`
- `runtime\backups`
- `runtime\temp`

The SQLite initialization and schema migration are idempotent and do not replace
an existing database.

## Backup and restore

```powershell
.\scripts\backup-tkai.ps1 -IncludeMediaManifest
.\scripts\restore-tkai.ps1 -Backup C:\Users\laow7\Documents\TKAI\runtime\backups\20260728T010203Z
```

Backups include the database, sanitized configuration, runtime metadata, an
optional media filename manifest, and SHA-256 integrity manifest. Retention is
configured by `backup_retention_count`. Restore requires an explicit backup,
validates integrity, refuses active services, creates a safety backup, requests
confirmation (or `-Force`), and writes an audit record.

## Diagnostics and logs

```powershell
.\scripts\diagnose-tkai.ps1
```

Diagnostics include versions, status, offline health, frontend build state, and
at most 100 recent lines from at most 20 local logs. Passwords, tokens, secrets,
cookies, sessions, and proxy credentials are redacted. Separate service logs and
startup, shutdown, health, backup, restore, and audit records live in
`runtime\logs`.

## Docker local deployment

Docker Desktop users can run:

```powershell
docker compose -f docker-compose.local.yml up --build -d
docker compose -f docker-compose.local.yml ps
docker compose -f docker-compose.local.yml down
```

The local profile binds application listeners to loopback and persists
`/runtime`. Use the native backup command after stopping containers, or copy the
named volume through an explicitly reviewed Docker volume workflow.

## Troubleshooting and upgrades

- Port conflict: stop the owning application or select three unique ports above
  1023 in `configuration\local.json`.
- Startup exit: inspect `runtime\logs\*-error.log`.
- Stale PID: `stop-tkai.ps1` safely removes it.
- Unhealthy database: stop services, take a backup, and run diagnostics before
  restoring.
- Upgrade: stop TKAI, back up, update the branch, rerun `setup-tkai.ps1`, run
  tests, then start and health-check. Startup never deletes user data.
