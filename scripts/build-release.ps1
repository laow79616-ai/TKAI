param([Parameter(Mandatory = $true)][string]$PytestSummary)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repository = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$python = Join-Path $repository ".venv\Scripts\python.exe"
$releaseInputs = @(
    "RELEASE_NOTES_V8.md",
    "FRAMEWORK_MANIFEST_V8.json",
    "RELEASE_NOTES_V7.md",
    "FRAMEWORK_MANIFEST.json",
    "INTEGRITY_MANIFEST.json",
    "RELEASE_MANIFEST_V8.json",
    "BUILD_METADATA.json"
)
foreach ($relative in $releaseInputs) {
    if (-not (Test-Path -LiteralPath (Join-Path $repository $relative))) {
        throw "Release input missing: $relative"
    }
}
# CHECKSUMS_V8.txt supersedes the historical SHA256SUMS catalog.
# $sourceArchive is produced as artifacts\tkai-8.0.0.tar.gz by the Python builder.
if (-not (Test-Path -LiteralPath $python)) {
    throw "Release Python environment is missing: $python"
}
& $python (Join-Path $PSScriptRoot "build-final-release.py") `
    --pytest-summary $PytestSummary
if ($LASTEXITCODE -ne 0) {
    throw "Final release asset generation failed."
}
