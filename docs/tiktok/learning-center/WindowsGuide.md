# Windows Guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_learning_center.py
.\.venv\Scripts\python.exe -m ruff check tiktok\learning_center tests\tiktok\test_learning_center.py
.\.venv\Scripts\python.exe -m mypy tiktok\learning_center
```

The tests use in-memory mock history only and require no TikTok network access,
credentials, browser, device, proxy, or publishing configuration.
