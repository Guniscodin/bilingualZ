@echo off
REM Development launcher. Build a real executable with packaging\build-windows.bat
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py %*
) else (
    python run.py %*
)
