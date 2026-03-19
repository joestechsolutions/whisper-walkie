@echo off
cd /d "%~dp0"
echo Starting Whisper Walkie (debug mode)...
echo Log file: %~dp0walkie.log
echo.
"venv\Scripts\python.exe" main.py
pause
