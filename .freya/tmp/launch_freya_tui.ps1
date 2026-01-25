$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'H:\Code\Freya2'

# Always use the venv python to ensure modules + editable install are visible
& 'H:\Code\Freya2\.venv\Scripts\python.exe' -m freya.cli tui
