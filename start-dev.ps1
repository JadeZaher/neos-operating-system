Write-Host "Starting NEOS API development server..." -ForegroundColor Cyan

# Create venv if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate venv
& .venv\Scripts\Activate.ps1

# Install deps
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -e "agent[dev]" --quiet

# Start server
Set-Location agent
Write-Host "Backend running at http://localhost:8000/dashboard" -ForegroundColor Green
python -m neos_agent.main --dev
