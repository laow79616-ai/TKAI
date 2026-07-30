# Windows Guide

From PowerShell at the repository root:

```powershell
.\\.venv\\Scripts\\python.exe -m pytest tests\\v8\\hyper_operations
.\\.venv\\Scripts\\python.exe -m ruff check src\\tkai\\v8\\hyper_operations tests\\v8\\hyper_operations
.\\.venv\\Scripts\\python.exe -m mypy src\\tkai\\v8\\hyper_operations
```

These commands use mocks and local metadata only. They do not require TikTok, a browser, accounts, proxies, devices, or a running operational environment.
