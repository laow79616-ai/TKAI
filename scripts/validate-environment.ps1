. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
if ($repository -ne "C:\Users\laow7\Documents\TKAI") { throw "Unexpected repository: $repository" }
$python = Join-Path $repository ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Missing .venv; run scripts\setup-local.ps1." }
$version = & $python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ([version]$version -lt [version]"3.10") { throw "Python 3.10+ is required." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js is required." }
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw "npm is required." }
foreach ($path in @("configuration\local.json", "dashboard\frontend\node_modules", "studio\frontend\node_modules")) {
    if (-not (Test-Path -LiteralPath (Join-Path $repository $path))) { throw "Missing dependency: $path" }
}
Write-Host "Environment valid: Python $version; Node $(& node --version); npm $(& npm.cmd --version); PowerShell $($PSVersionTable.PSVersion)"
