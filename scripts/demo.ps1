$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment Python was not found at $Python"
}

Write-Host "Installing project and dev dependencies..."
& $Python -m pip install --disable-pip-version-check -e ".[dev]"

Write-Host "Running test suite..."
& $Python -m pytest -q

Write-Host "Running offline GTM demo..."
& $Python -m gtm_engine.cli demo `
    --input "data/sample_prospects.csv" `
    --output "artifacts" `
    --config "config/scoring.yaml"

Write-Host "`nDemo summary:"
Get-Content "artifacts/summary.json"
Write-Host "`nProcessed records: artifacts/processed_prospects.json"
