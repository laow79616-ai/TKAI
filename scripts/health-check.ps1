param([switch]$Quiet)
. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
$config = Get-TkaiConfiguration $repository
$checks = @(
    @{ Name="backend health"; Url="http://$($config.backend_host):$($config.backend_port)/health" },
    @{ Name="readiness"; Url="http://$($config.backend_host):$($config.backend_port)/readiness" },
    @{ Name="liveness"; Url="http://$($config.backend_host):$($config.backend_port)/health" },
    @{ Name="dashboard"; Url="http://$($config.dashboard_host):$($config.dashboard_port)/" },
    @{ Name="AI Studio"; Url="http://$($config.studio_host):$($config.studio_port)/" }
)
$failed = 0
foreach ($check in $checks) {
    try { $response = Invoke-WebRequest -UseBasicParsing -Uri $check.Url -TimeoutSec 3; if ($response.StatusCode -ne 200) { throw "HTTP $($response.StatusCode)" }; if (-not $Quiet) { Write-Host "PASS $($check.Name)" } }
    catch { $failed++; if (-not $Quiet) { Write-Warning "FAIL $($check.Name): $($_.Exception.Message)" } }
}
if ($failed -ne 0) { throw "$failed health check(s) failed." }
