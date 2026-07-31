. "$PSScriptRoot\tkai-runtime-common.ps1"; $repository=Get-TkaiRepository $PSScriptRoot
$python=Join-Path $repository ".venv\Scripts\python.exe"; if (-not (Test-Path $python)) { throw "Run setup-local.ps1 first." }
& $python -m pip install --disable-pip-version-check -e "$repository[server,dev]"; exit $LASTEXITCODE
