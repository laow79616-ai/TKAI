# Windows Guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v7\observability_framework
.\.venv\Scripts\python.exe -m ruff check src\tkai\v7\observability_framework
.\.venv\Scripts\python.exe -m mypy src\tkai\v7\observability_framework
```

No Windows service, registry entry, external agent, or telemetry credential is
required.
