Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-TkaiRepository {
    param([string]$ScriptRoot)
    $repository = [System.IO.Path]::GetFullPath((Join-Path $ScriptRoot ".."))
    if (-not (Test-Path -LiteralPath (Join-Path $repository "pyproject.toml")) -or
        -not (Test-Path -LiteralPath (Join-Path $repository "tiktok"))) {
        throw "This script must be run from the TKAI repository scripts directory."
    }
    return $repository
}

function Get-TkaiConfiguration {
    param([string]$Repository)
    $path = Join-Path $Repository "configuration\local.json"
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing configuration\local.json. Copy configuration\local.example.json first."
    }
    $config = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
    foreach ($hostName in @("backend_host", "dashboard_host", "studio_host")) {
        if ($config.$hostName -notin @("127.0.0.1", "localhost", "::1")) {
            throw "$hostName must use loopback for local single-user mode."
        }
    }
    return $config
}

function Test-TkaiPort {
    param([string]$HostName, [int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $task = $client.ConnectAsync($HostName, $Port)
        return $task.Wait(300) -and $client.Connected
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Write-TkaiPidReference {
    param([string]$Repository, [string]$Service, [System.Diagnostics.Process]$Process, [string]$Command)
    $pids = Join-Path $Repository "runtime\pids"
    New-Item -ItemType Directory -Force -Path $pids | Out-Null
    @{
        service = $Service
        pid = $Process.Id
        command = $Command
        repository = $Repository
        created_at = [DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $pids "$Service.json")
}

function Stop-TkaiOwnedProcess {
    param([string]$Repository, [string]$Service)
    $pidFile = Join-Path $Repository "runtime\pids\$Service.json"
    if (-not (Test-Path -LiteralPath $pidFile)) {
        Write-Host "$Service`: no PID reference"
        return
    }
    try {
        $reference = Get-Content -Raw -LiteralPath $pidFile | ConvertFrom-Json
        if ($reference.service -ne $Service -or $reference.repository -ne $Repository) {
            throw "PID ownership check failed"
        }
        $process = Get-Process -Id $reference.pid -ErrorAction SilentlyContinue
        if ($null -ne $process) {
            $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($reference.pid)"
            $commandLine = $processInfo.CommandLine
            $fingerprint = switch ($Service) {
                "backend" { "server.api.app:create_app" }
                "dashboard" { "--prefix dashboard/frontend" }
                "studio" { "--prefix studio/frontend" }
            }
            if (
                $reference.command -notlike "*$fingerprint*" -or
                $commandLine -notlike "*$fingerprint*"
            ) {
                throw "Process command line is not owned by this TKAI checkout"
            }

            $owned = @($reference.pid)
            do {
                $children = @(Get-CimInstance Win32_Process | Where-Object {
                    $_.ParentProcessId -in $owned -and $_.ProcessId -notin $owned
                } | Select-Object -ExpandProperty ProcessId)
                $owned += $children
            } while ($children.Count -gt 0)
            [array]::Reverse($owned)
            foreach ($processId in $owned) {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
            [void]$process.WaitForExit(10000)
            Write-Host "$Service`: stopped"
        } else {
            Write-Host "$Service`: stale PID reference cleaned"
        }
        Remove-Item -LiteralPath $pidFile
    } catch {
        Write-Warning "$Service`: $($_.Exception.Message)"
    }
}
