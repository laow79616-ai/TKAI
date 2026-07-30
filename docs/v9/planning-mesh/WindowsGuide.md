# Windows Guide

Run validation from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v9\planning_mesh
.\.venv\Scripts\python.exe -m ruff check src\tkai\v9\planning_mesh
.\.venv\Scripts\python.exe -m mypy src\tkai\v9\planning_mesh
```

No external service, TikTok credential, scheduler, or resource manager is
required. Tests use local metadata only.
