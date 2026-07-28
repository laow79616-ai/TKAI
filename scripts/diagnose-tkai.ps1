param([string]$Output)
. "$PSScriptRoot\tkai-runtime-common.ps1"
$repository = Get-TkaiRepository $PSScriptRoot
$python = Join-Path $repository ".venv\Scripts\python.exe"
if (-not $Output) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $Output = Join-Path $repository "runtime\exports\diagnostics-$stamp.json"
}
& $python -m local_runtime.cli diagnose --repository $repository | Set-Content -Encoding UTF8 -LiteralPath $Output
Write-Host "Sanitized diagnostics written to $Output"
