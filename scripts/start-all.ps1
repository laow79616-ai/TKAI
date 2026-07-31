param([switch]$Development)
$ErrorActionPreference = "Stop"
try {
    & "$PSScriptRoot\validate-environment.ps1"
    & "$PSScriptRoot\start-tkai.ps1" -Development:$Development
    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    $ready = $false
    do {
        try { & "$PSScriptRoot\health-check.ps1" -Quiet; $ready = $true } catch { $ready = $false }
        if ($ready) { break }
        Start-Sleep -Seconds 1
    } while ([DateTime]::UtcNow -lt $deadline)
    if (-not $ready) { throw "Services did not become ready within 45 seconds." }
    & "$PSScriptRoot\health-check.ps1"
    Write-Host "Logs: runtime\logs"
} catch {
    Write-Error $_
    & "$PSScriptRoot\stop-all.ps1"
    throw
}
