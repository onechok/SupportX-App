#define MyAppName "SupportX App"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppPublisher "SupportX"
#define MyAppExe "start-supportx.bat"

[Setup]
AppId={{B9D55C45-53F9-4C85-B2A1-E55EA0D0D4B8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SupportX App
DefaultGroupName=SupportX App
OutputDir=..\..\dist
OutputBaseFilename=SupportX-Setup-v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\..\image\logo\logo-notification.ico
UninstallDisplayIcon={app}\image\logo\logo-notification.ico

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le Bureau"; GroupDescription: "Raccourcis:"; Flags: unchecked

[Files]
Source: "..\..\launcher.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\config\config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\config\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\install-supportx.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\install-supportx.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\start-supportx.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\start-supportx.sh"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\start-supportx.command"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\supportx_app\*"; DestDir: "{app}\supportx_app"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\..\image\*"; DestDir: "{app}\image"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\..\tabs\*"; DestDir: "{app}\tabs"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\SupportX App"; Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\image\logo\logo-notification.ico"
Name: "{commondesktop}\SupportX App"; Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\image\logo\logo-notification.ico"

[Run]
Filename: "{app}\install-supportx.bat"; Description: "Installer l'environnement Python et demarrer SupportX"; Flags: nowait postinstall skipifsilent
