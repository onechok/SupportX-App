@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist "%SCRIPT_DIR%launcher.py" (
    echo launcher.py introuvable. Verifiez le dossier SupportX-App.
    pause
    exit /b 1
)

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

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python "%SCRIPT_DIR%launcher.py"
    goto :eof
)

echo SupportX n'est pas encore installe correctement.
echo Lancement de l'installateur...
call "%SCRIPT_DIR%install-supportx.bat"
if errorlevel 1 (
    echo Installation annulee ou en echec.
    pause
    exit /b 1
)

if exist "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" (
    start "" "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" "%SCRIPT_DIR%launcher.py"
    goto :eof
)

echo Impossible de demarrer SupportX apres installation.
pause
exit /b 1
