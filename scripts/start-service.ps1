param([Parameter(Mandatory=$true)][ValidateSet("backend","dashboard","studio")][string]$Service, [switch]$Development)
. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository=Get-TkaiRepository $PSScriptRoot; $config=Get-TkaiConfiguration $repository
$python=Join-Path $repository ".venv\Scripts\python.exe"; $logs=Join-Path $repository "runtime\logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$hostName=$config."${Service}_host"; $port=[int]$config."${Service}_port"
if (Test-TkaiPort $hostName $port) { throw "Port $port for $Service is already in use." }
if ($Service -eq "backend") {
    $args=@("-m","uvicorn","--factory","server.api.app:create_app","--host",$hostName,"--port","$port"); $file=$python
} else {
    $folder=$(if ($Service -eq "dashboard") { "dashboard/frontend" } else { "studio/frontend" })
    $args=@("--prefix",$folder,"run",$(if ($Development) { "dev" } else { "preview" }),"--","--host",$hostName,"--port","$port"); $file="npm.cmd"
}
$process=Start-Process -FilePath $file -ArgumentList $args -WorkingDirectory $repository -RedirectStandardOutput "$logs\$Service.log" -RedirectStandardError "$logs\$Service-error.log" -PassThru -WindowStyle Hidden
Write-TkaiPidReference $repository $Service $process "$file $($args -join ' ')"
Start-Sleep -Seconds 1; if ($process.HasExited) { throw "$Service exited during startup; inspect runtime\logs." }
Write-Host "$Service started on http://$hostName`:$port"
