param(
    [Parameter(Mandatory=$true)]
    [string]$Module
)

Write-Host ""
Write-Host "========================================"
Write-Host " TKAI Developer"
Write-Host "========================================"
Write-Host ""

$target = "scripts\module-$Module.ps1"

if(Test-Path $target){
    Write-Host "Module already exists:"
    Write-Host "  $target"
}
else{
    New-Item -ItemType File -Path $target | Out-Null
    Write-Host "Created:"
    Write-Host "  $target"
}

Write-Host ""
Get-ChildItem scripts
