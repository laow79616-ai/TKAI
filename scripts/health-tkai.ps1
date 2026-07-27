. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
$python = Join-Path $repository ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { $python = "python" }
& $python -m local_runtime.cli health --repository $repository
exit $LASTEXITCODE
