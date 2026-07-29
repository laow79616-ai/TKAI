param([string]$OutputDirectory = "artifacts")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repository = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$output = [System.IO.Path]::GetFullPath((Join-Path $repository $OutputDirectory))
$release = Get-Content "$repository\release.json" -Raw | ConvertFrom-Json
$stage = Join-Path $output "tkai-$($release.version)"
$archive = Join-Path $output "tkai-$($release.version).zip"
$sourceArchive = Join-Path $output "tkai-$($release.version).tar.gz"

if (-not (Test-Path "$repository\dashboard\frontend\dist")) { throw "Dashboard build is missing." }
if (-not (Test-Path "$repository\studio\frontend\dist")) { throw "AI Studio build is missing." }
New-Item -ItemType Directory -Force -Path $output | Out-Null
if (Test-Path $sourceArchive) { Remove-Item -LiteralPath $sourceArchive -Force }
git -C $repository archive --format=tar.gz --prefix="tkai-$($release.version)/" `
    -o $sourceArchive HEAD
if ($LASTEXITCODE -ne 0) { throw "Source package generation failed." }
if (Test-Path $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }
New-Item -ItemType Directory -Path $stage | Out-Null

$include = @(
    "src", "server", "tiktok", "local_runtime", "dashboard\frontend\dist",
    "studio\frontend\dist", "configuration\local.example.json", "deployment",
    "scripts", "docs", "pyproject.toml", "README.md", "CHANGELOG.md",
    "RELEASE_NOTES_V7.md", "VERSION_SUMMARY.md", "LICENSE",
    "release.json", "release-checklist.json", "RELEASE_MANIFEST.json",
    "FRAMEWORK_MANIFEST.json", "INTEGRITY_MANIFEST.json",
    "BUILD_METADATA.json", "docs\Upgrade.md", "docs\KnownIssues.md",
    "docs\ProductionDeployment.md", "docker-compose.local.yml"
)
foreach ($relative in $include) {
    $source = Join-Path $repository $relative
    if (-not (Test-Path -LiteralPath $source)) { throw "Release input missing: $relative" }
    $destination = Join-Path $stage $relative
    New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
}
New-Item -ItemType Directory -Force -Path "$stage\source" | Out-Null
Copy-Item -LiteralPath $sourceArchive -Destination "$stage\source" -Force
Get-ChildItem $stage -Recurse -Directory | Where-Object {
    $_.Name -in @("__pycache__", "node_modules", "runtime", ".venv")
} | Sort-Object FullName -Descending | Remove-Item -Recurse -Force
Get-ChildItem $stage -Recurse -File | Where-Object {
    $_.Extension -in @(".pyc", ".log", ".db") -or
    $_.Name -match "\.(cookie|session|credential|secret)$"
} | Remove-Item -Force
$secretPattern = "-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}"
$secretHit = Get-ChildItem $stage -Recurse -File | Where-Object {
    $_.Length -le 5MB -and
    (Select-String -LiteralPath $_.FullName -Pattern $secretPattern -Quiet)
} | Select-Object -First 1
if ($secretHit) {
    throw "Potential secret found in release input: $($secretHit.FullName.Substring($stage.Length + 1))"
}

$commit = (git -C $repository rev-parse HEAD).Trim()
$metadata = Get-Content "$stage\release.json" -Raw | ConvertFrom-Json
$metadata.git_commit = $commit
$metadata | ConvertTo-Json | Set-Content "$stage\release.json" -Encoding UTF8
$buildMetadata = [ordered]@{
    product = $release.product
    version = $release.version
    git_commit = $commit
    built_at_utc = [DateTime]::UtcNow.ToString("o")
    python = (& python --version 2>&1).ToString()
    powershell = $PSVersionTable.PSVersion.ToString()
}
$buildMetadata | ConvertTo-Json | Set-Content "$stage\BUILD_METADATA.json" -Encoding UTF8
$releaseManifest = [ordered]@{
    version = $release.version
    git_commit = $commit
    source_distribution = "source/tkai-$($release.version).tar.gz"
    included_roots = $include
    file_count = @(Get-ChildItem $stage -Recurse -File).Count
}
$releaseManifest | ConvertTo-Json -Depth 3 |
    Set-Content "$stage\RELEASE_MANIFEST.json" -Encoding UTF8
Get-ChildItem $stage -Recurse -File | Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($stage.Length + 1).Replace("\", "/")
    "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower())  $relative"
} | Set-Content "$stage\SHA256SUMS" -Encoding ASCII
$integrityManifest = [ordered]@{
    schema_version = 1
    algorithm = "SHA-256"
    checksum_file = "SHA256SUMS"
    source_distribution = "source/tkai-$($release.version).tar.gz"
    generated_at_utc = [DateTime]::UtcNow.ToString("o")
}
$integrityManifest | ConvertTo-Json |
    Set-Content "$stage\INTEGRITY_MANIFEST.json" -Encoding UTF8
Compress-Archive -Path "$stage\*" -DestinationPath $archive -CompressionLevel Optimal
"$((Get-FileHash $archive -Algorithm SHA256).Hash.ToLower())  $(Split-Path $archive -Leaf)" |
    Set-Content "$archive.sha256" -Encoding ASCII
Write-Host $archive
