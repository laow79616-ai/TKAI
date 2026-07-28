# TKAI V5.0 Local Quick Start

TKAI V5.0 is a local, single-user TikTok Cloud Control Platform. It binds the
API, Dashboard, and AI Studio to loopback by default and requires no live TikTok
access for startup or health validation.

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,server]"
npm ci --prefix dashboard/frontend
npm ci --prefix studio/frontend
Copy-Item configuration/local.example.json configuration/local.json
.\scripts\setup-tkai.ps1
.\scripts\start-tkai.ps1
.\scripts\health-tkai.ps1
```

Open the Dashboard at `http://127.0.0.1:4173`, AI Studio at
`http://127.0.0.1:4174`, and API documentation at
`http://127.0.0.1:8000/docs`. Stop owned processes in reverse startup order
with `.\scripts\stop-tkai.ps1`. Create a verified backup before upgrades with
`.\scripts\backup-tkai.ps1`.
