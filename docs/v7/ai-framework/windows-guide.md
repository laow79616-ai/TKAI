# Windows Guide

From PowerShell, activate `.venv\Scripts\Activate.ps1`, install the repository
development dependencies, and run:

```powershell
python -m pytest tests\v7\ai_framework
python -m ruff check src\tkai\v7\ai_framework tests\v7\ai_framework
python -m mypy src\tkai\v7\ai_framework
```

No provider service, TikTok session, credential, or external network access is
needed.
