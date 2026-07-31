param([switch]$IncludeMediaManifest)
& "$PSScriptRoot\backup-tkai.ps1" -IncludeMediaManifest:$IncludeMediaManifest; exit $LASTEXITCODE
