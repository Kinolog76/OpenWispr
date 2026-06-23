; Inno Setup script for OpenWispr.
; 1) Build the app first:  build.bat   (creates dist\OpenWispr\)
; 2) Open this file in Inno Setup Compiler and press Compile (or run ISCC.exe).
; Output: Output\OpenWispr-Setup.exe

#define MyAppName "OpenWispr"
#define MyAppVersion "1.0"
#define MyAppExe "OpenWispr.exe"

[Setup]
AppId={{8F2A1C7E-4B3D-4E9A-9C21-1A2B3C4D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=OpenWispr
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=OpenWispr-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Install per-user, no admin rights needed.
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=app.ico
UninstallDisplayIcon={app}\{#MyAppExe}

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Запускать при входе в Windows"; GroupDescription: "Автозапуск:"

[Files]
; Bundle the entire PyInstaller output folder.
Source: "dist\OpenWispr\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent
