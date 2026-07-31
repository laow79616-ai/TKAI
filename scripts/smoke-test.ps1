$ErrorActionPreference = "Stop"
. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
$config = Get-TkaiConfiguration $repository
& "$PSScriptRoot\status-all.ps1" | Out-Host
& "$PSScriptRoot\health-check.ps1"; if ($LASTEXITCODE) { exit $LASTEXITCODE }
foreach ($url in @("http://$($config.backend_host):$($config.backend_port)/openapi.json", "http://$($config.backend_host):$($config.backend_port)/business/v1/health")) {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
    if ($response.StatusCode -ne 200) { throw "Smoke request failed: $url" }
}
foreach ($path in @("runtime\data", "runtime\logs", "runtime\exports")) {
    if (-not (Test-Path -LiteralPath (Join-Path $repository $path))) { throw "Missing runtime path: $path" }
}
Write-Host "Offline local smoke test passed."
exit 0
