param([Parameter(Mandatory=$true)][string]$Backup, [switch]$ConfirmReplace)
if (-not $ConfirmReplace) { throw "Restore is confirmation-gated. Review the manifest, then rerun with -ConfirmReplace." }
. "$PSScriptRoot\tkai-runtime-common.ps1"; $repository=Get-TkaiRepository $PSScriptRoot
$python=Join-Path $repository ".venv\Scripts\python.exe"
& $python -m local_runtime.cli restore --repository $repository --backup $Backup --force; exit $LASTEXITCODE
