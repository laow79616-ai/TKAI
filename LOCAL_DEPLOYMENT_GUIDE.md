# Local Deployment Guide

TKAI local mode binds only to loopback and stores runtime state under `runtime/`.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-local.ps1 -SkipPlaywright
powershell -ExecutionPolicy Bypass -File .\scripts\start-all.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\smoke-test.ps1
```

Configuration is read from `configuration/local.json`; create it from the tracked example. Never commit `.env`, credentials, cookies, sessions, or proxy secrets.
