$ErrorActionPreference = "Stop"

function Write-Section($t) {
    Write-Host ""
    Write-Host $t -ForegroundColor Magenta
    Write-Host ("─" * ($t.Length)) -ForegroundColor DarkGray
}

function Get-VenvPython {
    $py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { throw "Venv introuvable: $py. Fais d'abord: python -m venv .venv" }
    return $py
}

function Ensure-PipPackage([string]$pkg) {
    $py = Get-VenvPython
    & $py -c "import $pkg" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Install package: $pkg ..." -ForegroundColor Yellow
        & $py -m pip install -U $pkg
    }
}

function Invoke-Freya([string[]]$FreyaArgs) {
    Write-Host ("`n> freya " + ($FreyaArgs -join " ")) -ForegroundColor DarkGray
    & freya @FreyaArgs
    if ($LASTEXITCODE -ne 0) { throw "Freya a échoué (exit code=$LASTEXITCODE)." }
}

Write-Section "Freya Launcher (Modern)"

# Ensure deps for TUI
$py = Get-VenvPython
& $py -m pip install -U pip | Out-Null
Ensure-PipPackage "rich"
Ensure-PipPackage "textual"

# Ensure editable install
Write-Host "Installing Freya (editable)..." -ForegroundColor Cyan
& $py -m pip install -e $PSScriptRoot | Out-Null

Write-Host ""
Write-Host "1) Ouvrir Freya TUI (1 fenêtre : onglets + chat à droite)" -ForegroundColor Cyan
Write-Host "2) Bench standard (CLI)"
Write-Host "3) Status (CLI)"
Write-Host "0) Quitter"
$choice = Read-Host "Choix"

switch ($choice) {
    "1" {
        # Launch in Windows Terminal if available (fonts/themes live there)
        $wt = Get-Command wt -ErrorAction SilentlyContinue
        if ($wt) {
            Write-Host "Launching Windows Terminal..." -ForegroundColor Cyan
            Start-Process wt -ArgumentList @(
                "new-tab",
                "--title", "Freya TUI",
                "--startingDirectory", $PSScriptRoot,
                "powershell", "-NoExit", "-Command", "cd `"$PSScriptRoot`"; freya tui"
            ) | Out-Null
        }
        else {
            Write-Host "Windows Terminal (wt) non trouvé. Lancement dans la console actuelle." -ForegroundColor Yellow
            Invoke-Freya @("tui")
        }
    }
    "2" { Invoke-Freya @("bench-standard") }
    "3" { Invoke-Freya @("status") }
    "0" { return }
    default { Write-Host "Option invalide" -ForegroundColor Yellow }
}
