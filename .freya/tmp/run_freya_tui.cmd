@echo off
cd /d "H:\Code\Freya2"
"H:\Code\Freya2\.venv\Scripts\python.exe" -m freya.cli tui
echo.
echo Freya exited with code %ERRORLEVEL%
pause
