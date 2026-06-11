param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"

Set-Location $ProjectRoot

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Virtual environment not found at $Python. Run scripts\start_backend.ps1 first or create the venv manually."
}

$env:API_BASE_URL = $ApiBaseUrl

Write-Host "Starting Streamlit at http://$HostName`:$Port"
Write-Host "Using API_BASE_URL=$ApiBaseUrl"
& $Python -m streamlit run frontend/app.py --server.address $HostName --server.port $Port
