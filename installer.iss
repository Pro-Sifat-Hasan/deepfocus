; Inno Setup Installer Script for DeepFocus
; Install Inno Setup from https://jrsoftware.org/isinfo.php
; Then right-click this file and "Compile"
; The installer will be created at: dist\DeepFocus_Setup.exe

[Setup]
AppId={{C8F5E8D2-9A3B-4E1F-8C7D-6B5A4E3D2C1B}
AppName=DeepFocus
AppVersion=0.1.0
AppPublisher=NeuroBrain
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
DefaultDirName={autopf}\DeepFocus
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=dist
OutputBaseFilename=DeepFocus_Setup
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Require administrator privileges - installer will prompt for elevation via UAC
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog commandline
DefaultGroupName=DeepFocus
UninstallDisplayIcon={app}\deepfocus.exe
UninstallDisplayName=DeepFocus
VersionInfoCompany=NeuroBrain
VersionInfoProductName=DeepFocus
VersionInfoProductVersion=0.1.0
VersionInfoDescription=DeepFocus - Social Media Blocker
VersionInfoCopyright=Created by Sifat

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenu"; Description: "Create Start Menu shortcuts"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "autostart"; Description: "Start DeepFocus when Windows starts"; GroupDescription: "Options:"; Flags: checkedonce

[Files]
; Source files from build\windows directory (where Flet builds the executable)
; This copies all files including deepfocus.exe, DLLs, Lib folder, data folder, etc.
Source: "build\windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DeepFocus"; Filename: "{app}\deepfocus.exe"
Name: "{group}\{cm:UninstallProgram,DeepFocus}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DeepFocus"; Filename: "{app}\deepfocus.exe"; Tasks: desktopicon

[Run]
; Launch program after installation with admin privileges
; Use runascurrentuser to run as the installing user (not admin context)
; The EXE itself has a manifest that requests admin privileges when needed
Filename: "{app}\deepfocus.exe"; Description: "{cm:LaunchProgram,DeepFocus}"; Flags: nowait postinstall skipifsilent runascurrentuser

[Registry]
; Add to startup if task is selected - start minimized (in tray)
; HKCU doesn't require admin privileges, so this works even without elevation
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "DeepFocus"; ValueData: """{app}\deepfocus.exe"" --minimized"; Flags: uninsdeletevalue; Tasks: autostart
; Note: Inno Setup automatically creates HKLM uninstaller entries in:
; HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall\DeepFocus
; These are created with admin privileges when PrivilegesRequired=admin is set
; The UninstallDisplayName setting above ensures it shows as "DeepFocus" not "DeepFocus version 0.1.0"
