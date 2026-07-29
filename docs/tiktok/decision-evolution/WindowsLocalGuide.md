# Decision Evolution Center Windows Local Guide

From PowerShell in the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_decision_evolution.py
.\.venv\Scripts\python.exe -m ruff check tiktok\decision_evolution tests\tiktok\test_decision_evolution.py
.\.venv\Scripts\python.exe -m mypy tiktok\decision_evolution
```

Start the existing local API using the repository's normal Windows runtime
procedure. Then generate or inspect OpenAPI and confirm all
`/tiktok/decision-evolution/*` operations are GET. Do not place cookies, sessions,
proxy credentials, access tokens, or API secrets in profiles or logs.

Tests use bounded reference adapters and require no browser, TikTok account, proxy,
network access, publishing access, or CAPTCHA interaction.
