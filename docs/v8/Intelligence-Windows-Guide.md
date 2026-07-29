# Hyper Intelligence Windows Guide

From a PowerShell prompt at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v8\hyper_intelligence
.\.venv\Scripts\python.exe -m ruff check src\tkai\v8\hyper_intelligence
.\.venv\Scripts\python.exe -m mypy
```

Use the existing operational scripts under `scripts\` for local platform
lifecycle tasks. The intelligence fabric itself starts no process, opens no
network connection, and accesses no live TikTok service.
