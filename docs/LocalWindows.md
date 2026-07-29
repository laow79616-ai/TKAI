# TKAI V6.0 Local Windows Guide

Use PowerShell 7, Python 3.10 or newer, and a supported Node.js runtime. From
the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,server]"
npm --prefix dashboard/frontend ci
npm --prefix studio/frontend ci
.\scripts\setup-tkai.ps1
.\scripts\start-tkai.ps1
.\scripts\health-tkai.ps1
```

Keep runtime state under the configured runtime directory and secrets in
environment variables or an approved secret store. Use `status-tkai.ps1`,
`diagnose-tkai.ps1`, `backup-tkai.ps1`, and `stop-tkai.ps1` for operations.
Run scripts from the repository root so their path guards resolve correctly.

For release validation, build both frontends, run the Python validation suites,
then run `build-release.ps1` and `validate-release.ps1`. Do not use generated
`artifacts/` copies as import roots.
