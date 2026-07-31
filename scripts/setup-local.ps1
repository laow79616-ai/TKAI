param([switch]$SkipPlaywright)
& "$PSScriptRoot\setup-tkai.ps1" -SkipPlaywright:$SkipPlaywright
exit $LASTEXITCODE
