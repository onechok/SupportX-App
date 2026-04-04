$ErrorActionPreference = 'Stop'

function Write-Step {
    param([string]$Message)
    Write-Host "[SupportX] $Message"
}

function Find-SystemPython {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        try {
            $pyExe = py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $pyExe) {
                return $pyExe.Trim()
            }
        } catch {
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        try {
            $pyExe = python -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $pyExe) {
                return $pyExe.Trim()
            }
        } catch {
        }
    }

    return $null
}

function Install-PythonWithWinget {
    $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $wingetCmd) {
        return $false
    }

    Write-Step "Python n'est pas detecte. Installation via winget..."
    winget install --id Python.Python.3.13 -e --source winget --accept-package-agreements --accept-source-agreements --silent
    return ($LASTEXITCODE -eq 0)
}

function Ensure-Shortcut {
    param(
        [string]$Path,
        [string]$Target,
        [string]$WorkingDirectory,
        [string]$Icon
    )

    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($Path)
    $shortcut.TargetPath = $Target
    $shortcut.WorkingDirectory = $WorkingDirectory
    $shortcut.IconLocation = $Icon
    $shortcut.Save()
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
$requirementsPath = Join-Path $scriptDir "requirements.txt"
$startBat = Join-Path $scriptDir "start-supportx.bat"
$iconPath = Join-Path $scriptDir "image\logo\logo-notification.ico"

if (-not (Test-Path $venvPython)) {
    $systemPython = Find-SystemPython
    if (-not $systemPython) {
        $installed = Install-PythonWithWinget
        if ($installed) {
            $systemPython = Find-SystemPython
        }
    }

    if (-not $systemPython) {
        throw "Python 3.10+ introuvable. Installez Python puis relancez install-supportx.bat."
    }

    Write-Step "Creation de l'environnement virtuel..."
    & $systemPython -m venv (Join-Path $scriptDir ".venv")
}

Write-Step "Mise a jour de pip..."
& $venvPython -m pip install --upgrade pip

Write-Step "Installation des dependances du projet..."
& $venvPython -m pip install -r $requirementsPath

$desktopPath = [Environment]::GetFolderPath('Desktop')
$startMenuPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\SupportX.lnk"
$desktopShortcut = Join-Path $desktopPath "SupportX.lnk"

Write-Step "Creation des raccourcis..."
Ensure-Shortcut -Path $desktopShortcut -Target $startBat -WorkingDirectory $scriptDir -Icon $iconPath
Ensure-Shortcut -Path $startMenuPath -Target $startBat -WorkingDirectory $scriptDir -Icon $iconPath

Write-Step "Installation terminee."
Write-Step "L'application va demarrer..."
Start-Process -FilePath $startBat -WorkingDirectory $scriptDir
