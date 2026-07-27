. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
$log = Join-Path $repository "runtime\logs\shutdown.log"
"[$([DateTime]::UtcNow.ToString('o'))] shutdown requested" | Add-Content -Encoding UTF8 -LiteralPath $log
foreach ($service in @("studio", "dashboard", "backend")) {
    Stop-TkaiOwnedProcess $repository $service
}
Write-Host "TKAI shutdown complete. Logs and data were preserved."
