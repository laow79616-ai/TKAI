# Windows Guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_analytics_center.py
.\.venv\Scripts\python.exe -m ruff check tiktok\analytics_center
```

The center is fully testable with in-memory mocks and requires no live TikTok
connection.
