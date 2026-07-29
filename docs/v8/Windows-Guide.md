# Windows Guide

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v8\hyper_kernel
.\.venv\Scripts\python.exe -m ruff check src\tkai\v8 tests\v8
.\.venv\Scripts\python.exe -m mypy
Set-Location dashboard\frontend
npm.cmd run build
```

The Hyper Kernel requires no service, browser, TikTok credential, or network
connection. Do not put secrets in registry metadata; secret-like fields are
redacted, but callers should still provide references instead of secret values.
