# Windows Deployment Guide

Use PowerShell from the repository root:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev,server]"
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m mypy
.venv\Scripts\python.exe -m pytest
npm --prefix dashboard\frontend run build
npm --prefix studio\frontend run build
```

Run the API with the existing TKAI production configuration and service manager.
Do not place credentials in command lines, environment dumps, repository files,
or logs. Configure Account Center, Browser Runtime, Proxy Center, Workflow,
Automation, encrypted storage, API Gateway, observability, and audit sinks using
the platform deployment guides. Restrict network egress to approved endpoints
and validate tenant/workspace policies before enabling task execution.
