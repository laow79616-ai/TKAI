Write-Host ""
Write-Host "========================================"
Write-Host " TKAI Module-007"
Write-Host "========================================"
Write-Host ""

Write-Host "[1/3] Doctor"
python -m tkai doctor

Write-Host ""
Write-Host "[2/3] Template List"
python -m tkai template list

Write-Host ""
Write-Host "[3/3] Git Status"
git status
