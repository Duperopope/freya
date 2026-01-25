$ErrorActionPreference = "Stop"

function Get-VenvPython {
    $py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { throw "Venv introuvable: $py (crée-le avec: python -m venv .venv)" }
    return $py
}

function Update-Pip {
    $py = Get-VenvPython
    & $py -m pip install -U pip | Out-Null
}

function Install-PythonPackage([string]$name) {
    $py = Get-VenvPython
    & $py -c "import $name" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing $name ..." -ForegroundColor Yellow
        & $py -m pip install -U $name
    }
}

$py = Get-VenvPython
Update-Pip
Install-PythonPackage "rich"
Install-PythonPackage "textual"

Write-Host "Installing Freya (editable)..." -ForegroundColor Cyan
& $py -m pip install -e $PSScriptRoot | Out-Null

Write-Host "Launching Freya TUI..." -ForegroundColor Cyan
try {
    & freya tui
    exit $LASTEXITCODE
}
catch {
    & $py -m freya.cli tui
    exit $LASTEXITCODE
}
