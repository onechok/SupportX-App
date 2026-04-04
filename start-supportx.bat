@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" (
    start "" "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" "%SCRIPT_DIR%launcher.py"
    goto :eof
)

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    start "" "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%launcher.py"
    goto :eof
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" py "%SCRIPT_DIR%launcher.py"
    goto :eof
)

start "" python "%SCRIPT_DIR%launcher.py"
