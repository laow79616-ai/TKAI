. "$PSScriptRoot\tkai-runtime-common.ps1"; $repository=Get-TkaiRepository $PSScriptRoot
& npm.cmd --prefix (Join-Path $repository "dashboard\frontend") ci; exit $LASTEXITCODE
