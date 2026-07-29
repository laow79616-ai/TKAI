# Windows Guide

From PowerShell in the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v7\workflow_framework
.\.venv\Scripts\python.exe -m ruff check src\tkai\v7\workflow_framework
.\.venv\Scripts\python.exe -m mypy src\tkai\v7\workflow_framework
```

No browser or TikTok account is required; tests use local in-memory objects.
