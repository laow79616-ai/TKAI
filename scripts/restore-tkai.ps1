param(
    [Parameter(Mandatory = $true)][string]$Backup,
    [switch]$Force
)
. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
if (-not $Force) {
    $answer = Read-Host "Restore $Backup and replace inactive local state? Type RESTORE"
    if ($answer -ne "RESTORE") { throw "Restore cancelled." }
}
$python = Join-Path $repository ".venv\Scripts\python.exe"
& $python -m local_runtime.cli restore --repository $repository --backup $Backup --force
