<#
.SYNOPSIS
    Freya 2.0 Installation Script for Windows

.DESCRIPTION
    Installs Freya with all dependencies (Python + Node.js/Web UI)
    
.EXAMPLE
    .\install.ps1
    
.EXAMPLE
    .\install.ps1 -SkipWebUI
#>

param(
    [switch]$SkipWebUI,
    [switch]$DevMode
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Freya 2.0 Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "  Found: $pythonVersion" -ForegroundColor Green

# Check Node.js (for web UI)
if (-not $SkipWebUI) {
    Write-Host "[2/5] Checking Node.js..." -ForegroundColor Yellow
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Node.js not found. Web UI will not be built." -ForegroundColor Yellow
        Write-Host "  Install Node.js 18+ for the web interface." -ForegroundColor Yellow
        $SkipWebUI = $true
    } else {
        Write-Host "  Found: Node.js $nodeVersion" -ForegroundColor Green
    }
} else {
    Write-Host "[2/5] Skipping Node.js check (--SkipWebUI)" -ForegroundColor Gray
}

# Create virtual environment
Write-Host "[3/5] Setting up Python environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "  Created virtual environment" -ForegroundColor Green
} else {
    Write-Host "  Virtual environment exists" -ForegroundColor Green
}

# Activate and install Python package
Write-Host "[4/5] Installing Python dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

if ($DevMode) {
    pip install -e ".[dev]" --quiet
    Write-Host "  Installed in development mode" -ForegroundColor Green
} else {
    pip install -e . --quiet
    Write-Host "  Installed Freya package" -ForegroundColor Green
}

# Build web UI
if (-not $SkipWebUI) {
    Write-Host "[5/5] Building Web UI..." -ForegroundColor Yellow
    Push-Location web
    
    if (-not (Test-Path "node_modules")) {
        npm install --silent
    }
    
    npm run build --silent
    Pop-Location
    Write-Host "  Web UI built successfully" -ForegroundColor Green
} else {
    Write-Host "[5/5] Skipping Web UI build" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start Freya:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Activate the virtual environment" -ForegroundColor Gray
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  # Start the web server" -ForegroundColor Gray
Write-Host "  freya serve" -ForegroundColor White
Write-Host ""
Write-Host "  # Then open http://localhost:8765 in your browser" -ForegroundColor Gray
Write-Host ""

if (-not $SkipWebUI) {
    Write-Host "Web UI is ready at: http://localhost:8765" -ForegroundColor Green
} else {
    Write-Host "Note: Web UI not built. API-only mode available." -ForegroundColor Yellow
    Write-Host "  Run 'cd web && npm install && npm run build' to build the UI." -ForegroundColor Yellow
}
Write-Host ""
