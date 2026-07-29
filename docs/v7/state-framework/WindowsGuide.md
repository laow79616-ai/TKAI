# Windows Guide

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v7\state_framework
.\.venv\Scripts\python.exe -m ruff check --no-cache src\tkai\v7\state_framework tests\v7\state_framework
.\.venv\Scripts\python.exe -m mypy --cache-dir work\mypy src\tkai\v7\state_framework
```

No service, external datastore, or TikTok connection is required.
