# ClearWayAI Windows PowerShell Bootstrap Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  ClearWayAI - Monorepo Bootstrap & Environment Setup     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/5] Checking Python environment..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.10+."
    exit 1
}

# 2. Check Node.js and Package Manager
Write-Host "`n[2/5] Checking Node.js environment..." -ForegroundColor Yellow
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "Found Node: $nodeVersion" -ForegroundColor Green
} else {
    Write-Error "Node.js is not installed. Please install Node.js 18+."
    exit 1
}

# 3. Environment File
Write-Host "`n[3/5] Checking configuration (.env)..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example (DEFAULT: SIMULATION_ONLY=true, DEMO_FIXTURE)" -ForegroundColor Green
} else {
    Write-Host ".env already exists." -ForegroundColor Gray
}

# 4. Install Python Dependencies
Write-Host "`n[4/5] Checking Python dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "Python dependencies verified." -ForegroundColor Green
} else {
    Write-Warning "Failed to install some Python dependencies."
}

# 5. Install Node Dependencies
Write-Host "`n[5/5] Installing Node dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -eq 0) {
    Write-Host "Node dependencies installed successfully." -ForegroundColor Green
} else {
    Write-Warning "npm install returned warning/error."
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " Bootstrap Complete! You can now run:" -ForegroundColor Green
Write-Host "   - Backend: python -m uvicorn apps.api.src.main:app --reload --port 8000" -ForegroundColor White
Write-Host "   - Frontend: npm --prefix apps/web run dev" -ForegroundColor White
Write-Host "   - Tests:    pytest -v" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
