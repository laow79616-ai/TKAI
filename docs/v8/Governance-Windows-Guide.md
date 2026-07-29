# V8 Governance Windows Guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v8\hyper_governance
.\.venv\Scripts\python.exe -m ruff check src\tkai\v8\hyper_governance
.\.venv\Scripts\python.exe -m mypy
```

Start TKAI through the supported scripts under `scripts\`. Query the governance
health and metadata endpoints with `Invoke-RestMethod`. Do not add credentials
to governance metadata; recognized secret keys are redacted, but source systems
remain responsible for secret storage.

```powershell
Invoke-RestMethod http://localhost:8000/v8/governance/health
```

All governance endpoints are GET-only. No operation triggers TikTok access.
