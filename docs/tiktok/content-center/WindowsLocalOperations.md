# Windows Local Operations Guide

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pytest
npm --prefix dashboard\frontend run build
npm --prefix studio\frontend run build
git diff --check
```

The Content Center uses in-memory bounded adapters in tests and requires no live
TikTok connection. For a local API host, install the `server` optional dependency
and use the existing server startup process. Do not put storage credentials,
account sessions, cookies or proxy secrets into project metadata or environment
files committed to source control.

When diagnosing publishing, inspect scoped audit records and Prometheus metrics,
then verify Account Center, Browser Runtime, Proxy Center and Account Farming in
that order. Keep approval enforcement enabled outside isolated tests.
