$ErrorActionPreference = "Stop"

$scriptPath = $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($scriptPath)) { throw "Lance via .\freya.ps1" }
$root = Split-Path -Parent $scriptPath

$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Venv introuvable: $py" }

& $py -m pip install -U pip | Out-Null
& $py -c "import rich" 2>$null; if ($LASTEXITCODE -ne 0) { & $py -m pip install -U rich | Out-Null }
& $py -c "import textual" 2>$null; if ($LASTEXITCODE -ne 0) { & $py -m pip install -U textual | Out-Null }

& $py -m pip install -e $root | Out-Null

# Standalone PowerShell window (no wt)
$psExe = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$cmd = "Set-Location -LiteralPath `"$root`"; & `"$py`" -m freya.cli tui"

Start-Process -FilePath $psExe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $cmd
) | Out-Null
