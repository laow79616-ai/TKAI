param([switch]$Confirm)
if (-not $Confirm) { throw "Cache cleanup requires -Confirm." }
. "$PSScriptRoot\tkai-runtime-common.ps1"; $repository=Get-TkaiRepository $PSScriptRoot
foreach ($path in @(".pytest_cache", ".ruff_cache", ".mypy_cache")) { $target=Join-Path $repository $path; if (Test-Path $target) { Remove-Item -Recurse -Force -LiteralPath $target } }
Write-Host "Local tool caches removed; application data was not changed."
