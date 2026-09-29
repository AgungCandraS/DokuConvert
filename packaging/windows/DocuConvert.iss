#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#ifndef PayloadDir
  #error PayloadDir must point to the PyInstaller DocuConvert folder
#endif
#ifndef OutputDir
  #error OutputDir must point to a new release output folder
#endif
#ifndef ProjectRoot
  #error ProjectRoot must point to the repository root
#endif

[Setup]
AppId={{D7A4EAA5-9F4D-4937-AD06-57E91F0C942C}
AppName=DocuConvert
AppVersion={#AppVersion}
AppPublisher=DocuConvert
DefaultDirName={localappdata}\Programs\DocuConvert
DefaultGroupName=DocuConvert
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\DocuConvert.exe
SetupIconFile="{#ProjectRoot}\app\ui\resources\icons\app-icon.ico"
OutputDir="{#OutputDir}"
OutputBaseFilename=DocuConvert-Setup-{#AppVersion}-windows-x64
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes
DisableProgramGroupPage=yes
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Shortcut tambahan:"

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\DocuConvert"; Filename: "{app}\DocuConvert.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\DocuConvert"; Filename: "{app}\DocuConvert.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\DocuConvert.exe"; Description: "Jalankan DocuConvert"; Flags: postinstall nowait skipifsilent
