# V7 Windows Guide

Use PowerShell from the repository root:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pytest
```

Build the dashboard and AI Studio from their frontend directories with
`npm run build`. V7 does not install services, modify the registry, alter
execution policy, or start background processes. Extension paths use Python
dotted paths (`package.module:extension`) and are independent of Windows path
separators.
