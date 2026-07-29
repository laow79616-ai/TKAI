# Windows Local Guide

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_predictive_analytics.py
.\.venv\Scripts\python.exe -m ruff check tiktok\predictive_analytics tests\tiktok\test_predictive_analytics.py
.\.venv\Scripts\python.exe -m mypy tiktok\predictive_analytics
```

The implementation and tests use local mock/reference adapters only. Do not
configure TikTok credentials.
