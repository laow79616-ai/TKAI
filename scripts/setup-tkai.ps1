param([switch]$SkipPlaywright)
. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
Set-Location -LiteralPath $repository

if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3.10+ is required." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js 20+ is required." }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "npm is required." }
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pythonVersion -lt [version]"3.10") { throw "Python 3.10+ is required." }

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) { python -m venv .venv }
& ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -e ".[server,dev]"
npm --prefix dashboard/frontend ci
npm --prefix studio/frontend ci
if (-not $SkipPlaywright) {
    & ".venv\Scripts\python.exe" -m playwright install chromium
}
if (-not (Test-Path -LiteralPath "configuration\local.json")) {
    Copy-Item -LiteralPath "configuration\local.example.json" -Destination "configuration\local.json"
}
& ".venv\Scripts\python.exe" -m local_runtime.cli init --repository $repository
npm --prefix dashboard/frontend run build
npm --prefix studio/frontend run build
Write-Host "TKAI local environment is ready."
