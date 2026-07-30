# Hyper Decision Windows Guide

From PowerShell at the repository root:

```powershell
python -m pytest tests\v8\hyper_decision
python -m ruff check src\tkai\v8\hyper_decision tests\v8\hyper_decision
python -m mypy src\tkai\v8\hyper_decision
```

No service, TikTok connection, or secret is needed. The package uses immutable
in-memory mockable metadata. Operational scripts in `scripts\` should be parsed with
the PowerShell parser before release.
