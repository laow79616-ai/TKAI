# Campaign Center Windows Guide

From PowerShell in the repository root:

```powershell
.\scripts\start-tkai.ps1
```

Open the local dashboard and select `tiktok-campaign-center`. Keep all service
bindings on the configured loopback interface. Stop the local runtime with:

```powershell
.\scripts\stop-tkai.ps1
```

Run offline validation with the repository virtual environment:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\mypy.exe
.\.venv\Scripts\pytest.exe
```

No live TikTok account or network access is required by Campaign Center tests.
