# Windows Guide

From PowerShell in the repository root, run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v10\governance_mesh
.\.venv\Scripts\python.exe -m ruff check src\tkai\v10\governance_mesh
```

The tests are offline and do not launch a browser, authenticate to TikTok, or
access the network.
