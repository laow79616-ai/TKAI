# Windows Local Guide

Run from the repository root in PowerShell:

```powershell
.\scripts\start-tkai.ps1
```

Open the local dashboard and select `tiktok-autonomous-strategy-center`. Stop
the runtime with:

```powershell
.\scripts\stop-tkai.ps1
```

No live TikTok connection is required for strategy scenarios or tests. Keep
credentials in the existing local secret/reference infrastructure, never in
strategy metadata.
