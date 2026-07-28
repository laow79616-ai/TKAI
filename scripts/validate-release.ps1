param([string]$Archive = "artifacts\tkai-4.0.0.zip")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repository = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$path = [System.IO.Path]::GetFullPath((Join-Path $repository $Archive))
if (-not (Test-Path -LiteralPath $path)) { throw "Release archive not found: $path" }
$forbidden = @(
    "(^|/)node_modules/",
    "(^|/)\.venv/",
    "(^|/)runtime/",
    "\.db$",
    "\.(cookie|session|credential|secret)$",
    "\.log$"
)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($path)
try {
    $names = @($zip.Entries | ForEach-Object {
        $_.FullName.ToLowerInvariant().Replace("\", "/")
    })
    foreach ($term in $forbidden) {
        if ($names | Where-Object { $_ -match $term }) { throw "Forbidden release entry: $term" }
    }
    foreach ($required in @("release.json", "release-checklist.json", "sha256sums", "configuration/local.example.json")) {
        if (-not ($names | Where-Object { $_ -like "*/$required" -or $_ -eq $required })) {
            throw "Required release entry missing: $required"
        }
    }
} finally {
    $zip.Dispose()
}
$expected = (Get-Content "$path.sha256").Split(" ")[0]
$actual = (Get-FileHash $path -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) { throw "Release archive checksum mismatch." }
Write-Host "Release package validation passed."
