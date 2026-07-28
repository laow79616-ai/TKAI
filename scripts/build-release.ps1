param([string]$OutputDirectory = "artifacts")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repository = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$output = [System.IO.Path]::GetFullPath((Join-Path $repository $OutputDirectory))
$stage = Join-Path $output "tkai-4.0.0"
$archive = Join-Path $output "tkai-4.0.0.zip"

if (-not (Test-Path "$repository\dashboard\frontend\dist")) { throw "Dashboard build is missing." }
if (-not (Test-Path "$repository\studio\frontend\dist")) { throw "AI Studio build is missing." }
New-Item -ItemType Directory -Force -Path $output | Out-Null
if (Test-Path $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }
New-Item -ItemType Directory -Path $stage | Out-Null

$include = @(
    "src", "server", "tiktok", "local_runtime", "dashboard\frontend\dist",
    "studio\frontend\dist", "configuration\local.example.json", "deployment",
    "scripts", "docs", "pyproject.toml", "README.md", "LICENSE",
    "release.json", "release-checklist.json", "docker-compose.local.yml"
)
foreach ($relative in $include) {
    $source = Join-Path $repository $relative
    if (-not (Test-Path -LiteralPath $source)) { throw "Release input missing: $relative" }
    $destination = Join-Path $stage $relative
    New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
}
Get-ChildItem $stage -Recurse -Directory | Where-Object {
    $_.Name -in @("__pycache__", "node_modules", "runtime", ".venv")
} | Sort-Object FullName -Descending | Remove-Item -Recurse -Force
Get-ChildItem $stage -Recurse -File | Where-Object {
    $_.Extension -in @(".pyc", ".log", ".db") -or
    $_.Name -match "\.(cookie|session|credential|secret)$"
} | Remove-Item -Force

$commit = (git -C $repository rev-parse HEAD).Trim()
$metadata = Get-Content "$stage\release.json" -Raw | ConvertFrom-Json
$metadata.git_commit = $commit
$metadata | ConvertTo-Json | Set-Content "$stage\release.json" -Encoding UTF8
Get-ChildItem $stage -Recurse -File | Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($stage.Length + 1).Replace("\", "/")
    "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower())  $relative"
} | Set-Content "$stage\SHA256SUMS" -Encoding ASCII
Compress-Archive -Path "$stage\*" -DestinationPath $archive -CompressionLevel Optimal
"$((Get-FileHash $archive -Algorithm SHA256).Hash.ToLower())  $(Split-Path $archive -Leaf)" |
    Set-Content "$archive.sha256" -Encoding ASCII
Write-Host $archive
