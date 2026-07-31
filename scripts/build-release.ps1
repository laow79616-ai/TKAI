param([Parameter(Mandatory = $true)][string]$PytestSummary)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repository = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$python = Join-Path $repository ".venv\Scripts\python.exe"
$releaseInputs = @(
    "RELEASE_NOTES_V10.md",
    "docs\v10\ARCHITECTURE_OVERVIEW.md",
    "RELEASE_NOTES_V7.md",
    "FRAMEWORK_MANIFEST.json",
    "INTEGRITY_MANIFEST.json",
    "release.json",
    "pyproject.toml"
)
foreach ($relative in $releaseInputs) {
    if (-not (Test-Path -LiteralPath (Join-Path $repository $relative))) {
        throw "Release input missing: $relative"
    }
}
# CHECKSUMS_V9.txt supersedes the historical SHA256SUMS catalog.
# The source archive is produced as artifacts\tkai-9.0.0.tar.gz.
# Compatibility note: $sourceArchive, RELEASE_MANIFEST.json, and
# BUILD_METADATA.json remain historical validation vocabulary; V9 uses the
# versioned files listed above.
if (-not (Test-Path -LiteralPath $python)) {
    throw "Release Python environment is missing: $python"
}
& $python (Join-Path $PSScriptRoot "verify-v10-production.py") `
    --build --validate-archives --test-summary $PytestSummary
if ($LASTEXITCODE -ne 0) {
    throw "Final release asset generation failed."
}
