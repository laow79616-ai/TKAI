# Windows Guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\tkai\v7\runtime_governance tests\v7\runtime_governance
.\.venv\Scripts\python.exe -m mypy src\tkai\v7\runtime_governance
.\.venv\Scripts\python.exe -m pytest tests\v7\runtime_governance
```

No browser, TikTok session, live runtime, or network service is required.
