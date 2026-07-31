param([string]$Output)
& "$PSScriptRoot\diagnose-tkai.ps1" -Output $Output; exit $LASTEXITCODE
