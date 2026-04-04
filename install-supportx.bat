@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

where py >nul 2>nul
if %errorlevel%==0 (
    if not exist "%SCRIPT_DIR%.venv" py -3 -m venv "%SCRIPT_DIR%.venv"
    "%SCRIPT_DIR%.venv\Scripts\python.exe" -m pip install --upgrade pip
    "%SCRIPT_DIR%.venv\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%requirements.txt"
) else (
    if not exist "%SCRIPT_DIR%.venv" python -m venv "%SCRIPT_DIR%.venv"
    "%SCRIPT_DIR%.venv\Scripts\python.exe" -m pip install --upgrade pip
    "%SCRIPT_DIR%.venv\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%requirements.txt"
)

set "DESKTOP_SHORTCUT=%USERPROFILE%\Desktop\SupportX.lnk"
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "STARTMENU_SHORTCUT=%STARTMENU_DIR%\SupportX.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); ^
$Shortcut.TargetPath = '%SCRIPT_DIR%start-supportx.bat'; ^
$Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; ^
$Shortcut.IconLocation = '%SCRIPT_DIR%image\logo\logo-notification.ico'; ^
$Shortcut.Save(); ^
$Shortcut2 = $WshShell.CreateShortcut('%STARTMENU_SHORTCUT%'); ^
$Shortcut2.TargetPath = '%SCRIPT_DIR%start-supportx.bat'; ^
$Shortcut2.WorkingDirectory = '%SCRIPT_DIR%'; ^
$Shortcut2.IconLocation = '%SCRIPT_DIR%image\logo\logo-notification.ico'; ^
$Shortcut2.Save();"

echo Installation terminee.
echo Lance l'application avec le raccourci SupportX sur le Bureau ou depuis le menu Demarrer.
