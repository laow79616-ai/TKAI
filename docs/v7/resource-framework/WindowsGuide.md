# Windows Guide

From PowerShell, use the repository virtual environment and run:

```powershell
python -m pytest tests\v7\resource_framework
python -m ruff check src\tkai\v7\resource_framework tests\v7\resource_framework
python -m mypy
git diff --check
```

Use Windows paths only for local tooling. Resource, reservation, trend, and
recovery references should remain portable URI-shaped identifiers. No browser,
account, proxy, device, worker, or TikTok runtime is needed for tests.
