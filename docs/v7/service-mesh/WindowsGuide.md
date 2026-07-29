# Windows Guide

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v7\service_mesh
.\.venv\Scripts\python.exe -m ruff check src\tkai\v7\service_mesh tests\v7\service_mesh
.\.venv\Scripts\python.exe -m mypy src\tkai\v7\service_mesh
```

The mesh requires no Windows service, port, firewall rule, or administrator
privilege. References are in-process identifiers and do not resolve through the
network.
