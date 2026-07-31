# Windows Guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v11
.\.venv\Scripts\python.exe -m ruff check src\tkai\v11 tests\v11
.\.venv\Scripts\python.exe -m mypy src\tkai
```

These commands are offline and do not start TKAI services or browser sessions.
