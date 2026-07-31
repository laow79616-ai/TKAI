# Local Setup Guide

Prerequisites are Git, Python 3.10+, compatible Node/npm, and PowerShell.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,server]" build pip-audit
npm --prefix dashboard/frontend ci
npm --prefix studio/frontend ci
python scripts/validate-enterprise.py
```

Copy `.env.example` to untracked `.env` only when needed and never use production secrets locally.
