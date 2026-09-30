#ifndef AppVersion
  #define AppVersion "0.1.1"
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
AppId={code:InstallAppId}
UsePreviousLanguage=no
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
LZMADictionarySize=131072
LZMANumFastBytes=273
LZMANumBlockThreads=1
LZMAUseSeparateProcess=yes
SolidCompression=yes
DisableProgramGroupPage=yes
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Shortcut tambahan:"

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\DocuConvert"; Filename: "{app}\DocuConvert.exe"; WorkingDir: "{app}"; Check: IsNormalInstall
Name: "{userdesktop}\DocuConvert"; Filename: "{app}\DocuConvert.exe"; WorkingDir: "{app}"; Tasks: desktopicon; Check: IsNormalInstall

[Run]
Filename: "{app}\DocuConvert.exe"; Description: "Jalankan DocuConvert"; Flags: postinstall nowait skipifsilent
Filename: "{app}\DocuConvert.exe"; Flags: nowait; Check: IsUpdate

[Code]
function IsNormalInstall: Boolean;
begin
  Result := ExpandConstant('{param:VERIFY|0}') <> '1';
end;

function InstallAppId(Param: String): String;
begin
  Result := '{D7A4EAA5-9F4D-4937-AD06-57E91F0C942C}';
  if not IsNormalInstall then
    Result := Result + '-verification';
end;

function IsUpdate: Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), '/UPDATE') = 0 then
      Result := True;
end;
