param([switch]$Development)
. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
$config = Get-TkaiConfiguration $repository
$python = Join-Path $repository ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Run scripts\setup-tkai.ps1 first." }
foreach ($tool in @("node", "npm")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "$tool is required." }
}
foreach ($service in @(
    @{ Name = "backend"; Host = $config.backend_host; Port = $config.backend_port },
    @{ Name = "dashboard"; Host = $config.dashboard_host; Port = $config.dashboard_port },
    @{ Name = "studio"; Host = $config.studio_host; Port = $config.studio_port }
)) {
    if (Test-TkaiPort $service.Host $service.Port) {
        throw "Port $($service.Port) for $($service.Name) is already in use."
    }
}
& $python -m local_runtime.cli init --repository $repository | Out-Null
$logs = Join-Path $repository "runtime\logs"
"[$([DateTime]::UtcNow.ToString('o'))] startup requested" | Add-Content -Encoding UTF8 -LiteralPath "$logs\startup.log"

try {
    $backendArgs = @("-m", "uvicorn", "--factory", "server.api.app:create_app", "--host", $config.backend_host, "--port", "$($config.backend_port)")
    $backend = Start-Process -FilePath $python -ArgumentList $backendArgs -WorkingDirectory $repository -RedirectStandardOutput "$logs\backend.log" -RedirectStandardError "$logs\backend-error.log" -PassThru -WindowStyle Hidden
    Write-TkaiPidReference $repository "backend" $backend "$python $($backendArgs -join ' ')"

    $dashboardArgs = @("--prefix", "dashboard/frontend", "exec", "vite", "--", $(if ($Development) { "dev" } else { "preview" }), "--host", $config.dashboard_host, "--port", "$($config.dashboard_port)")
    $dashboard = Start-Process -FilePath "npm.cmd" -ArgumentList $dashboardArgs -WorkingDirectory $repository -RedirectStandardOutput "$logs\dashboard.log" -RedirectStandardError "$logs\dashboard-error.log" -PassThru -WindowStyle Hidden
    Write-TkaiPidReference $repository "dashboard" $dashboard "npm.cmd $($dashboardArgs -join ' ')"

    $studioArgs = @("--prefix", "studio/frontend", "exec", "vite", "--", $(if ($Development) { "dev" } else { "preview" }), "--host", $config.studio_host, "--port", "$($config.studio_port)")
    $studio = Start-Process -FilePath "npm.cmd" -ArgumentList $studioArgs -WorkingDirectory $repository -RedirectStandardOutput "$logs\studio.log" -RedirectStandardError "$logs\studio-error.log" -PassThru -WindowStyle Hidden
    Write-TkaiPidReference $repository "studio" $studio "npm.cmd $($studioArgs -join ' ')"

    Start-Sleep -Seconds 2
    foreach ($process in @($backend, $dashboard, $studio)) {
        if ($process.HasExited) { throw "A TKAI service exited during startup. Inspect runtime\logs." }
    }
} catch {
    & "$PSScriptRoot\stop-tkai.ps1"
    throw
}
Write-Host "TKAI started:"
Write-Host "  API:       http://$($config.backend_host):$($config.backend_port)"
Write-Host "  Dashboard: http://$($config.dashboard_host):$($config.dashboard_port)"
Write-Host "  AI Studio: http://$($config.studio_host):$($config.studio_port)"
