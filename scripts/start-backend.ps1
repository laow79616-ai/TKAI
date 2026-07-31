param([switch]$Development)
& "$PSScriptRoot\start-service.ps1" -Service backend -Development:$Development
