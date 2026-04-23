@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist "%SCRIPT_DIR%install-supportx.ps1" (
    echo install-supportx.ps1 introuvable.
    exit /b 1
)

where powershell >nul 2>nul
if %errorlevel%==0 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install-supportx.ps1"
) else (
    where pwsh >nul 2>nul
    if %errorlevel%==0 (
        pwsh -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install-supportx.ps1"
    ) else (
        echo Ni powershell ni pwsh n'est disponible sur cette machine.
        exit /b 1
    )
)

if errorlevel 1 (
    echo.
    echo Echec de l'installation SupportX.
    echo Verifiez votre connexion internet et relancez install-supportx.bat.
    pause
    exit /b 1
)

exit /b 0
