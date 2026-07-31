& "$PSScriptRoot\stop-all.ps1"; if ($LASTEXITCODE) { exit $LASTEXITCODE }; & "$PSScriptRoot\start-all.ps1"; exit $LASTEXITCODE
