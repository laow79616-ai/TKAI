# Windows Local Operations Guide

From PowerShell in the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_risk_control.py
.\.venv\Scripts\python.exe -m ruff check tiktok\risk_control tests\tiktok\test_risk_control.py
.\.venv\Scripts\python.exe -m mypy tiktok\risk_control
```

Start the existing API using the repository's documented local command. Open the dashboard route `tiktok-ai-risk-control-center`. Use only mock or bounded adapters in local testing; no test requires live TikTok access or plaintext credentials.
