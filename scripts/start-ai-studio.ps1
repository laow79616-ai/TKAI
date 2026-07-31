param([switch]$Development)
& "$PSScriptRoot\start-service.ps1" -Service studio -Development:$Development
