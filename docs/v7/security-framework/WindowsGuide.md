# Windows Guide

From the repository root in PowerShell:

```powershell
python -m pytest tests\v7\security_framework
python -m ruff check src\tkai\v7\security_framework tests\v7\security_framework
python -m mypy
git diff --check
```

Keep secret values in environment variables or the existing local credential
facility and register only `env://NAME` references. The framework requires no
Windows service, browser, or remote security endpoint.
