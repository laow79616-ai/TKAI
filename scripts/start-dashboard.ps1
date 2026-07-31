param([switch]$Development)
& "$PSScriptRoot\start-service.ps1" -Service dashboard -Development:$Development
