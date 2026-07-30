# Windows Guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v9\governance_mesh
.\.venv\Scripts\python.exe -m ruff check src\tkai\v9\governance_mesh
.\.venv\Scripts\python.exe -m mypy src\tkai\v9\governance_mesh
```

No TikTok credentials or network access are required. Tests use local mocks
and metadata only.
