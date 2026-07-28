# Windows Local Guide

From PowerShell, activate `.venv`, start TKAI with `scripts\start-tkai.ps1`, and open
the local dashboard. The Resource Center API is under
`/tiktok/resource-center/`. Stop with `scripts\stop-tkai.ps1`.

Validate locally with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_resource_center.py
.\.venv\Scripts\python.exe -m ruff check tiktok\resource_center tests\tiktok\test_resource_center.py
npm --prefix dashboard\frontend run build
```

All tests use local mocks and require no live TikTok access.
