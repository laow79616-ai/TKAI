# Hyper Reasoning Windows Guide

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v8\hyper_reasoning
.\.venv\Scripts\python.exe -m ruff check src\tkai\v8\hyper_reasoning tests\v8\hyper_reasoning
.\.venv\Scripts\python.exe -m mypy
```

No TikTok credentials, network access, or live services are required. Tests use
mock metadata only. Operational PowerShell scripts under `scripts\` should be
validated with the repository's existing script validation tests. Known
non-operational template files outside `scripts\` are not part of that check.
