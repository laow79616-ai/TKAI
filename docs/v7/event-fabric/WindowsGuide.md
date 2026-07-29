# Windows Guide

From `C:\Users\laow7\Documents\TKAI`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v7\event_fabric
.\.venv\Scripts\python.exe -m ruff check --no-cache src\tkai\v7\event_fabric tests\v7\event_fabric
.\.venv\Scripts\python.exe -m mypy --cache-dir work\mypy src\tkai\v7\event_fabric
```

The framework needs no broker, browser, network service, account, cookie, session,
or proxy. Operators should pause or engage the kill switch before shutdown, drain
only bounded batches, and require an audit and approval reference for replay.
