# Windows Guide

Run the existing local platform scripts from PowerShell:

```powershell
scripts\setup-tkai.ps1
scripts\start-tkai.ps1
```

Open the dashboard and use the GET-only `/tiktok/knowledge/*` endpoints. Build
the frontends with:

```powershell
npm --prefix dashboard/frontend run build
npm --prefix studio/frontend run build
```

Stop with `scripts\stop-tkai.ps1`. The center requires no live TikTok access,
additional daemon, external account, or secret.
