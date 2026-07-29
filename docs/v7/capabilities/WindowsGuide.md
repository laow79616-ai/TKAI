# Windows Guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v7\capabilities
.\.venv\Scripts\python.exe -m ruff check src\tkai\v7\capabilities
.\.venv\Scripts\python.exe -m mypy src\tkai
```

The framework uses only in-process Python contracts and requires no service,
network access, live TikTok credentials, or platform-specific daemon.
