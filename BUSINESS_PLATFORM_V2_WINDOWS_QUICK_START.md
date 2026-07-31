# TKAI Business Platform V2 Windows Quick Start

```powershell
cd C:\Users\laow7\Documents\TKAI
powershell -ExecutionPolicy Bypass -File .\scripts\start-all.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\status-all.ps1
```

Open `http://127.0.0.1:4173`. API docs are at `http://127.0.0.1:8000/docs` and AI
Studio at `http://127.0.0.1:4174`. Stop safely with
`powershell -ExecutionPolicy Bypass -File .\scripts\stop-all.ps1`.
