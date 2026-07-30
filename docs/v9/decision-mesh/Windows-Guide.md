# Windows Guide

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\tkai\v9\decision_mesh tests\v9\decision_mesh
.\.venv\Scripts\python.exe -m mypy src\tkai\v9\decision_mesh
.\.venv\Scripts\python.exe -m pytest tests\v9\decision_mesh -q
```
