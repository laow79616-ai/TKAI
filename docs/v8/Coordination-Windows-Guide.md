# V8 Coordination Windows Guide

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v8\hyper_coordination
.\.venv\Scripts\python.exe -m ruff check src\tkai\v8\hyper_coordination
.\.venv\Scripts\python.exe -m mypy
```

The framework is in-process and metadata-only. It needs no TikTok credentials,
browser session, worker, or network connection. Use the operational scripts
under `scripts\` for repository validation; non-operational templates outside
that directory are not part of this feature.
