# Startup and Shutdown

Start with `powershell -ExecutionPolicy Bypass -File .\scripts\start-all.ps1`. It validates dependencies and ports, starts all three services, waits for health, and prints URLs. Stop with `powershell -ExecutionPolicy Bypass -File .\scripts\stop-all.ps1`; restart with `scripts/restart-all.ps1`. A nonzero exit code indicates failure.
