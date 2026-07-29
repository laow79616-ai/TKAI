# Windows Guide

Use the repository virtual environment from PowerShell and create manifests in
trusted internal Python composition. Do not scan user profiles, load DLLs,
invoke scripts, use entry points, or contact plugin repositories.

Run focused tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v7\extension_framework -q
```

The framework performs no platform-specific process launch and stores no
Windows credentials.
