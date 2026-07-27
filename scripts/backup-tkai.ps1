param([switch]$IncludeMediaManifest)
. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
$python = Join-Path $repository ".venv\Scripts\python.exe"
$arguments = @("-m", "local_runtime.cli", "backup", "--repository", $repository)
if ($IncludeMediaManifest) { $arguments += "--include-media-manifest" }
& $python @arguments
