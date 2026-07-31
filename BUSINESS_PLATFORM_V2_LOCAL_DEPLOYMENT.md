# TKAI Business Platform V2 Local Deployment

From the repository root:

```powershell
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\scripts\setup-local.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start-all.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\health-check.ps1
```

Defaults are API `127.0.0.1:8000`, Dashboard `127.0.0.1:4173`, and AI Studio
`127.0.0.1:4174`. Override ports through `.env`. PID metadata ensures stop/restart
operations affect only owned processes. Stop with `scripts/stop-all.ps1`.
