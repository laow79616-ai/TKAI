# Hyper Knowledge Windows Guide

From PowerShell at the repository root, activate `.venv`, then run Python tools
with `python -m`. Use `npm ci` and `npm run build` under `dashboard/frontend` and
`studio/frontend`. Operational scripts under `scripts/` can be parsed without
execution by `[System.Management.Automation.Language.Parser]::ParseFile`.

The fabric uses in-memory metadata and needs no Windows service, database, or
TikTok credential.
