; Inno Setup 6 script for Pix42
; Docs: https://jrsoftware.org/ishelp/
;
; Prerequisites before compiling:
;   1. Run build_windows.bat to produce output\dist\Pix42\
;   2. Convert assets/app/icon.svg to assets/app/icon.ico
;      (Inkscape CLI: inkscape icon.svg -o icon.ico  -- or any online tool)

#define AppName      "Pix42"
#define AppVersion   "1.0.0"
#define AppPublisher "DemaHub"
#define AppExeName   "Pix42.exe"
#define AppId        "{{C4F8A2E1-7B3D-4F5C-9A12-8E6D3F7B1C4A}"

; ---------------------------------------------------------------------------
[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppId={#AppId}
DefaultDirName={commonpf64}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=output
OutputBaseFilename=Pix42-{#AppVersion}-Setup-Windows_x64
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
CreateUninstallRegKey=yes
CloseApplications=yes
RestartApplications=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

; ---------------------------------------------------------------------------
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

; ---------------------------------------------------------------------------
[Tasks]
; Additional icons
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; Shell integration
Name: "contextmenu"; Description: """Open with Pix42"" in right-click menu"; \
    GroupDescription: "Shell integration:"

; File associations (sets Pix42 as the default application)
Name: "assoc_images"; Description: "Common images  (.jpg  .jpeg  .png  .bmp  .gif  .webp  .tif  .tiff  .ico  .svg  .heic  .heif)"; \
    GroupDescription: "File associations (sets Pix42 as default):"; Flags: unchecked
Name: "assoc_raw";    Description: "RAW camera files  (.cr2  .cr3  .nef  .arw  .dng  .rw2  .raf  .orf  ...)"; \
    GroupDescription: "File associations (sets Pix42 as default):"; Flags: unchecked
Name: "assoc_fits";   Description: "FITS astronomical images  (.fit  .fits  .fts)"; \
    GroupDescription: "File associations (sets Pix42 as default):"; Flags: unchecked
Name: "assoc_psd";    Description: "Adobe Photoshop documents  (.psd)"; \
    GroupDescription: "File associations (sets Pix42 as default):"; Flags: unchecked

; ---------------------------------------------------------------------------
[Files]
Source: "output\dist\Pix42\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ---------------------------------------------------------------------------
[InstallDelete]
; Clean up the previous installation folder on upgrade
Type: filesandordirs; Name: "{app}"

; ---------------------------------------------------------------------------
[Icons]
Name: "{group}\{#AppName}";                       Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";                 Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

; ---------------------------------------------------------------------------
[Registry]

; ── ProgIDs ──────────────────────────────────────────────────────────────────

; Pix42.ImageFile  (JPEG, PNG, TIFF, BMP, GIF, WEBP, ICO, …)
Root: HKA; Subkey: "Software\Classes\Pix42.ImageFile"; \
    ValueType: string; ValueName: ""; ValueData: "Image File"; Flags: uninsdeletekey; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\Pix42.ImageFile\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\Pix42.ImageFile\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_images

; Pix42.RawFile  (camera RAW)
Root: HKA; Subkey: "Software\Classes\Pix42.RawFile"; \
    ValueType: string; ValueName: ""; ValueData: "RAW Camera Image"; Flags: uninsdeletekey; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\Pix42.RawFile\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\Pix42.RawFile\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_raw

; Pix42.FitsFile  (FITS astronomical images)
Root: HKA; Subkey: "Software\Classes\Pix42.FitsFile"; \
    ValueType: string; ValueName: ""; ValueData: "FITS Astronomical Image"; Flags: uninsdeletekey; Tasks: assoc_fits
Root: HKA; Subkey: "Software\Classes\Pix42.FitsFile\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_fits
Root: HKA; Subkey: "Software\Classes\Pix42.FitsFile\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_fits

; Pix42.PsdFile  (Photoshop)
Root: HKA; Subkey: "Software\Classes\Pix42.PsdFile"; \
    ValueType: string; ValueName: ""; ValueData: "Photoshop Document"; Flags: uninsdeletekey; Tasks: assoc_psd
Root: HKA; Subkey: "Software\Classes\Pix42.PsdFile\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_psd
Root: HKA; Subkey: "Software\Classes\Pix42.PsdFile\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_psd

; ── Extension → ProgID mappings ──────────────────────────────────────────────

; Common images (Pillow)
Root: HKA; Subkey: "Software\Classes\.jpg";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.jpeg"; ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.png";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.bmp";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.gif";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.webp"; ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.tif";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.tiff"; ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.ico";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.ppm";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.pgm";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.pbm";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.svg";  ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.heic"; ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images
Root: HKA; Subkey: "Software\Classes\.heif"; ValueType: string; ValueName: ""; ValueData: "Pix42.ImageFile"; Flags: uninsdeletevalue; Tasks: assoc_images

; RAW camera files (rawpy / libraw)
Root: HKA; Subkey: "Software\Classes\.cr2";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.cr3";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.nef";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.nrw";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.arw";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.srf";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.sr2";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.rw2";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.raf";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.orf";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.dng";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.pef";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.x3f";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.kdc";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.dcr";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.mrw";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.3fr";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.mef";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.erf";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.rwl";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw
Root: HKA; Subkey: "Software\Classes\.iiq";  ValueType: string; ValueName: ""; ValueData: "Pix42.RawFile"; Flags: uninsdeletevalue; Tasks: assoc_raw

; FITS astronomical images (astropy)
Root: HKA; Subkey: "Software\Classes\.fit";  ValueType: string; ValueName: ""; ValueData: "Pix42.FitsFile"; Flags: uninsdeletevalue; Tasks: assoc_fits
Root: HKA; Subkey: "Software\Classes\.fits"; ValueType: string; ValueName: ""; ValueData: "Pix42.FitsFile"; Flags: uninsdeletevalue; Tasks: assoc_fits
Root: HKA; Subkey: "Software\Classes\.fts";  ValueType: string; ValueName: ""; ValueData: "Pix42.FitsFile"; Flags: uninsdeletevalue; Tasks: assoc_fits

; Photoshop (psd-tools)
Root: HKA; Subkey: "Software\Classes\.psd";  ValueType: string; ValueName: ""; ValueData: "Pix42.PsdFile";  Flags: uninsdeletevalue; Tasks: assoc_psd

; ── Application registration ("Open with" shows "Pix42", not "pix42.exe") ────
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExeName}"; \
    ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#AppName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExeName}\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""

; App Paths — lets Windows locate the executable by name (e.g. Run dialog)
Root: HKA; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{#AppExeName}"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{#AppExeName}"; \
    ValueType: string; ValueName: "Path"; ValueData: "{app}"

; ── Context menu "Open with Pix42" (appears on all file types) ───────────────
; Uses HKLM\Software\Classes\*\shell which Windows merges into HKCR\*\shell.
Root: HKA; Subkey: "Software\Classes\*\shell\Pix42"; \
    ValueType: string; ValueName: "";      ValueData: "Open with Pix42"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\*\shell\Pix42"; \
    ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#AppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\*\shell\Pix42\command"; \
    ValueType: string; ValueName: "";      ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: contextmenu

; ---------------------------------------------------------------------------
[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; \
    Flags: nowait postinstall skipifsilent

; ---------------------------------------------------------------------------
[Code]

// Notify Windows Explorer that file associations have changed
procedure SHChangeNotify(wEventId: LongInt; uFlags: Cardinal; dwItem1: DWORD; dwItem2: DWORD);
  external 'SHChangeNotify@shell32.dll stdcall';

// ── Upgrade detection ────────────────────────────────────────────────────────

function GetUninstallString: String;
var
  sPath, sVal: String;
begin
  sPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1');
  if not RegQueryStringValue(HKLM, sPath, 'UninstallString', sVal) then
    RegQueryStringValue(HKCU, sPath, 'UninstallString', sVal);
  Result := sVal;
end;

function IsUpgrade: Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UninstallOldVersion: Integer;
var
  sUninstall: String;
  iCode: Integer;
begin
  Result := 0;
  sUninstall := GetUninstallString();
  if sUninstall <> '' then begin
    sUninstall := RemoveQuotes(sUninstall);
    if Exec(sUninstall, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, iCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

function InitializeSetup: Boolean;
begin
  Result := True;
  if IsUpgrade() then begin
    if MsgBox(
      'A previous version of {#AppName} is installed and will be removed before installing the new version.' + #13#13 +
      'Continue?',
      mbConfirmation, MB_YESNO) = IDNO then
      Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then begin
    if IsUpgrade() then
      UninstallOldVersion();
  end;

  // Tell Windows Explorer to refresh its file-type cache
  if CurStep = ssPostInstall then begin
    if WizardIsTaskSelected('assoc_images') or WizardIsTaskSelected('assoc_raw') or
       WizardIsTaskSelected('assoc_fits')   or WizardIsTaskSelected('assoc_psd') then
      SHChangeNotify($08000000, $0000, 0, 0);  // SHCNE_ASSOCCHANGED
  end;
end;
