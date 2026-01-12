# Create Single-File Installer for DeepFocus
# This creates a self-extracting PowerShell installer that bundles everything

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DeepFocus - Creating Single Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if distribution folder exists
$DistFolder = "dist\DeepFocus"
if (-not (Test-Path $DistFolder)) {
    Write-Host "ERROR: Distribution folder not found: $DistFolder" -ForegroundColor Red
    Write-Host "Please run .\build_windows.ps1 first." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "$DistFolder\deepfocus.exe")) {
    Write-Host "ERROR: deepfocus.exe not found." -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Creating installer package..." -ForegroundColor Yellow

# Create temporary directory for installer
$TempDir = "dist\installer_temp"
if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

# Create the installer PowerShell script
$installerScript = @'
# DeepFocus Installer Script
# This script is embedded in the installer executable

$ErrorActionPreference = "Stop"

# Extract files from embedded archive
function Extract-Files {
    param([string]$ArchivePath, [string]$ExtractPath)
    
    # Create extraction directory
    if (-not (Test-Path $ExtractPath)) {
        New-Item -ItemType Directory -Path $ExtractPath -Force | Out-Null
    }
    
    # Expand archive
    Expand-Archive -Path $ArchivePath -DestinationPath $ExtractPath -Force
}

# Main installation
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DeepFocus - Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" -Wait
    exit
}

# Get installation directory
$installDir = "$env:ProgramFiles\DeepFocus"
Write-Host "Installing to: $installDir" -ForegroundColor Cyan

# Create installation directory
if (Test-Path $installDir) {
    Write-Host "Removing existing installation..." -ForegroundColor Yellow
    Remove-Item $installDir -Recurse -Force
}
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

# Find and extract embedded archive
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
$archivePath = Join-Path $scriptDir "DeepFocus_Data.zip"

if (Test-Path $archivePath) {
    Write-Host "Extracting files..." -ForegroundColor Yellow
    Extract-Files -ArchivePath $archivePath -ExtractPath $installDir
} else {
    Write-Host "ERROR: Embedded archive not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create Start Menu shortcuts
Write-Host "Creating shortcuts..." -ForegroundColor Yellow
$startMenu = [Environment]::GetFolderPath("Programs")
$startMenuDir = Join-Path $startMenu "DeepFocus"
if (-not (Test-Path $startMenuDir)) {
    New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
}

$exePath = Join-Path $installDir "deepfocus.exe"
$desktop = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$desktopShortcut = $shell.CreateShortcut((Join-Path $desktop "DeepFocus.lnk"))
$desktopShortcut.TargetPath = $exePath
$desktopShortcut.WorkingDirectory = $installDir
$desktopShortcut.Description = "DeepFocus - Social Media Blocker"
$desktopShortcut.Save()

# Start Menu shortcut
$startShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "DeepFocus.lnk"))
$startShortcut.TargetPath = $exePath
$startShortcut.WorkingDirectory = $installDir
$startShortcut.Description = "DeepFocus - Social Media Blocker"
$startShortcut.Save()

# Add to registry for Add/Remove Programs
$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DeepFocus"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "DisplayName" -Value "DeepFocus - Social Media Blocker"
Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "$installDir\Uninstall.exe"
Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value $exePath
Set-ItemProperty -Path $regPath -Name "Publisher" -Value "NeuroBrain"
Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value "0.1.0"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "DeepFocus has been installed to: $installDir" -ForegroundColor Cyan
Write-Host "Shortcuts have been created on Desktop and Start Menu" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now launch DeepFocus from the Desktop or Start Menu." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
'@

# Save installer script
$installerScriptPath = Join-Path $TempDir "install.ps1"
$installerScript | Out-File -FilePath $installerScriptPath -Encoding UTF8

Write-Host "  Installer script created" -ForegroundColor Green

Write-Host ""
Write-Host "[2/3] Creating archive..." -ForegroundColor Yellow

# Create zip archive of distribution folder
$archivePath = Join-Path $TempDir "DeepFocus_Data.zip"
Compress-Archive -Path "$DistFolder\*" -DestinationPath $archivePath -Force

Write-Host "  Archive created: $(Split-Path -Leaf $archivePath)" -ForegroundColor Green

Write-Host ""
Write-Host "[3/3] Creating installer executable..." -ForegroundColor Yellow

# Create the final installer by combining script and archive
# We'll create a PowerShell script that extracts itself
$finalInstallerScript = @"
# Self-Extracting DeepFocus Installer
# DO NOT EDIT - AUTO-GENERATED

`$ErrorActionPreference = "Stop"

# Extract embedded archive
function Extract-EmbeddedArchive {
    `$scriptPath = `$MyInvocation.MyCommand.Path
    `$scriptDir = Split-Path -Parent `$scriptPath
    `$tempArchive = Join-Path `$env:TEMP "DeepFocus_Data_`$([Guid]::NewGuid().ToString().Substring(0,8)).zip"
    
    # Find the archive marker in this script
    `$scriptContent = Get-Content `$scriptPath -Raw -Encoding Byte
    `$marker = [System.Text.Encoding]::ASCII.GetBytes("#ARCHIVE_START#")
    `$markerIndex = [System.Array]::IndexOf(`$scriptContent, `$marker[0])
    
    if (`$markerIndex -ge 0) {
        # Extract archive data after marker
        `$archiveStart = `$markerIndex + `$marker.Length
        `$archiveData = `$scriptContent[`$archiveStart..(`$scriptContent.Length-1)]
        [System.IO.File]::WriteAllBytes(`$tempArchive, `$archiveData)
        return `$tempArchive
    }
    return `$null
}

# Installation logic
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DeepFocus - Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin
`$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not `$isAdmin) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    `$scriptPath = `$MyInvocation.MyCommand.Path
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File ``"`$scriptPath``"" -Wait
    exit
}

# Extract archive
Write-Host "Extracting files..." -ForegroundColor Yellow
`$tempArchive = Extract-EmbeddedArchive
if (-not `$tempArchive -or -not (Test-Path `$tempArchive)) {
    Write-Host "ERROR: Failed to extract embedded archive!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install location
`$installDir = "`$env:ProgramFiles\DeepFocus"
if (Test-Path `$installDir) {
    Remove-Item `$installDir -Recurse -Force
}
New-Item -ItemType Directory -Path `$installDir -Force | Out-Null

# Extract to install directory
Expand-Archive -Path `$tempArchive -DestinationPath `$installDir -Force
Remove-Item `$tempArchive -Force

# Create shortcuts
Write-Host "Creating shortcuts..." -ForegroundColor Yellow
`$startMenu = [Environment]::GetFolderPath("Programs")
`$startMenuDir = Join-Path `$startMenu "DeepFocus"
if (-not (Test-Path `$startMenuDir)) {
    New-Item -ItemType Directory -Path `$startMenuDir -Force | Out-Null
}

`$exePath = Join-Path `$installDir "deepfocus.exe"
`$desktop = [Environment]::GetFolderPath("Desktop")
`$shell = New-Object -ComObject WScript.Shell

`$desktopShortcut = `$shell.CreateShortcut((Join-Path `$desktop "DeepFocus.lnk"))
`$desktopShortcut.TargetPath = `$exePath
`$desktopShortcut.WorkingDirectory = `$installDir
`$desktopShortcut.Description = "DeepFocus - Social Media Blocker"
`$desktopShortcut.Save()

`$startShortcut = `$shell.CreateShortcut((Join-Path `$startMenuDir "DeepFocus.lnk"))
`$startShortcut.TargetPath = `$exePath
`$startShortcut.WorkingDirectory = `$installDir
`$startShortcut.Description = "DeepFocus - Social Media Blocker"
`$startShortcut.Save()

# Registry
`$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DeepFocus"
New-Item -Path `$regPath -Force | Out-Null
Set-ItemProperty -Path `$regPath -Name "DisplayName" -Value "DeepFocus - Social Media Blocker"
Set-ItemProperty -Path `$regPath -Name "DisplayIcon" -Value `$exePath
Set-ItemProperty -Path `$regPath -Name "Publisher" -Value "NeuroBrain"
Set-ItemProperty -Path `$regPath -Name "DisplayVersion" -Value "0.1.0"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "DeepFocus has been installed successfully!" -ForegroundColor Green
Write-Host "Location: `$installDir" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"

#ARCHIVE_START#
"@

# Read archive as bytes
$archiveBytes = [System.IO.File]::ReadAllBytes($archivePath)

# Convert script to bytes and append archive
$scriptBytes = [System.Text.Encoding]::UTF8.GetBytes($finalInstallerScript)
$finalBytes = $scriptBytes + [System.Text.Encoding]::ASCII.GetBytes("#ARCHIVE_START#") + $archiveBytes

# Write final installer
$outputInstaller = "dist\DeepFocus_Installer.exe"
[System.IO.File]::WriteAllBytes($outputInstaller, $finalBytes)

# However, PowerShell scripts can't be directly executed as .exe
# So we'll create a batch file wrapper instead that's simpler
$batchInstaller = @"
@echo off
setlocal enabledelayedexpansion

echo ========================================
echo DeepFocus - Installation
echo ========================================
echo.

REM Check admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set INSTALL_DIR=%ProgramFiles%\DeepFocus

echo Installing to: %INSTALL_DIR%
echo.

REM Extract embedded files
set TEMP_DIR=%TEMP%\DeepFocus_Extract_%RANDOM%
mkdir "%TEMP_DIR%"

REM Find archive start marker in this batch file
REM Simple approach: extract using PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$archiveData = Get-Content '%~f0' -Raw -Encoding Byte; ^
     $marker = [byte[]](0x23, 0x41, 0x52, 0x43, 0x48, 0x49, 0x56, 0x45, 0x5F, 0x53, 0x54, 0x41, 0x52, 0x54, 0x23); ^
     $markerIndex = [System.Array]::IndexOf($archiveData, 0x23); ^
     if ($markerIndex -ge 0) { ^
         $archiveStart = $markerIndex + 15; ^
         $zipData = $archiveData[$archiveStart..($archiveData.Length-1)]; ^
         $zipPath = '%TEMP%\DeepFocus.zip'; ^
         [System.IO.File]::WriteAllBytes($zipPath, $zipData); ^
         Expand-Archive -Path $zipPath -DestinationPath '%TEMP_DIR%' -Force; ^
         Remove-Item $zipPath -Force ^
     }"

if not exist "%TEMP_DIR%\deepfocus.exe" (
    echo ERROR: Failed to extract files!
    pause
    exit /b 1
)

REM Install
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%"
xcopy /E /I /Y "%TEMP_DIR%\*" "%INSTALL_DIR%\"

REM Create shortcuts (using PowerShell)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$shell = New-Object -ComObject WScript.Shell; ^
     $desktop = [Environment]::GetFolderPath('Desktop'); ^
     $shortcut = $shell.CreateShortcut((Join-Path $desktop 'DeepFocus.lnk')); ^
     $shortcut.TargetPath = '%INSTALL_DIR%\deepfocus.exe'; ^
     $shortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
     $shortcut.Description = 'DeepFocus - Social Media Blocker'; ^
     $shortcut.Save(); ^
     $startMenu = [Environment]::GetFolderPath('Programs'); ^
     $startMenuDir = Join-Path $startMenu 'DeepFocus'; ^
     if (-not (Test-Path $startMenuDir)) { New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null }; ^
     $startShortcut = $shell.CreateShortcut((Join-Path $startMenuDir 'DeepFocus.lnk')); ^
     $startShortcut.TargetPath = '%INSTALL_DIR%\deepfocus.exe'; ^
     $startShortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
     $startShortcut.Description = 'DeepFocus - Social Media Blocker'; ^
     $startShortcut.Save()"

REM Cleanup
rmdir /s /q "%TEMP_DIR%"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo DeepFocus has been installed successfully!
echo Location: %INSTALL_DIR%
echo.
pause

#ARCHIVE_START#
"@

# Actually, let's use a simpler approach: Create a PowerShell script installer that's easy to use
# We'll use a different method - create a .ps1 file that can be renamed to .exe if user has PS2EXE
# Or we can create a batch file installer

# Simple approach: Create a self-contained PowerShell installer
$simpleInstaller = Get-Content (Join-Path $TempDir "install.ps1") -Raw
$archiveContent = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($archivePath))

$selfContainedInstaller = @"
# DeepFocus Installer - Self-Contained
# Run this script to install DeepFocus

`$ErrorActionPreference = "Stop"

# Check admin
`$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not `$isAdmin) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    `$scriptPath = `$MyInvocation.MyCommand.Path
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File ``"`$scriptPath``"" -Wait
    exit
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DeepFocus - Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Extract embedded archive
`$base64Archive = @"
$archiveContent
"@

`$tempArchive = Join-Path `$env:TEMP "DeepFocus_`$([Guid]::NewGuid().ToString().Substring(0,8)).zip"
`$archiveBytes = [Convert]::FromBase64String(`$base64Archive)
[System.IO.File]::WriteAllBytes(`$tempArchive, `$archiveBytes)

# Install location
`$installDir = "`$env:ProgramFiles\DeepFocus"
Write-Host "Installing to: `$installDir" -ForegroundColor Cyan

if (Test-Path `$installDir) {
    Write-Host "Removing existing installation..." -ForegroundColor Yellow
    Remove-Item `$installDir -Recurse -Force
}
New-Item -ItemType Directory -Path `$installDir -Force | Out-Null

# Extract
Write-Host "Extracting files..." -ForegroundColor Yellow
Expand-Archive -Path `$tempArchive -DestinationPath `$installDir -Force
Remove-Item `$tempArchive -Force

# Create shortcuts
Write-Host "Creating shortcuts..." -ForegroundColor Yellow
`$startMenu = [Environment]::GetFolderPath("Programs")
`$startMenuDir = Join-Path `$startMenu "DeepFocus"
if (-not (Test-Path `$startMenuDir)) {
    New-Item -ItemType Directory -Path `$startMenuDir -Force | Out-Null
}

`$exePath = Join-Path `$installDir "deepfocus.exe"
`$desktop = [Environment]::GetFolderPath("Desktop")
`$shell = New-Object -ComObject WScript.Shell

`$desktopShortcut = `$shell.CreateShortcut((Join-Path `$desktop "DeepFocus.lnk"))
`$desktopShortcut.TargetPath = `$exePath
`$desktopShortcut.WorkingDirectory = `$installDir
`$desktopShortcut.Description = "DeepFocus - Social Media Blocker"
`$desktopShortcut.Save()

`$startShortcut = `$shell.CreateShortcut((Join-Path `$startMenuDir "DeepFocus.lnk"))
`$startShortcut.TargetPath = `$exePath
`$startShortcut.WorkingDirectory = `$installDir
`$startShortcut.Description = "DeepFocus - Social Media Blocker"
`$startShortcut.Save()

# Registry
`$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DeepFocus"
New-Item -Path `$regPath -Force -ErrorAction SilentlyContinue | Out-Null
Set-ItemProperty -Path `$regPath -Name "DisplayName" -Value "DeepFocus - Social Media Blocker" -Force
Set-ItemProperty -Path `$regPath -Name "DisplayIcon" -Value `$exePath -Force
Set-ItemProperty -Path `$regPath -Name "Publisher" -Value "NeuroBrain" -Force
Set-ItemProperty -Path `$regPath -Name "DisplayVersion" -Value "0.1.0" -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "DeepFocus has been installed successfully!" -ForegroundColor Green
Write-Host "Location: `$installDir" -ForegroundColor Cyan
Write-Host "You can now launch DeepFocus from Desktop or Start Menu." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
"@

# Save the PowerShell installer (as backup)
$finalInstallerPath = "dist\DeepFocus_Installer.ps1"
$selfContainedInstaller | Out-File -FilePath $finalInstallerPath -Encoding UTF8

Write-Host "  PowerShell installer created" -ForegroundColor Green

# Create IExpress installer (single EXE file)
Write-Host ""
Write-Host "Creating single EXE installer using IExpress..." -ForegroundColor Yellow

# Create IExpress SED file
$sedContent = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=0
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%AppName% Installation
DisplayLicense=
FinishMessage=DeepFocus has been installed successfully! You can now launch it from Desktop or Start Menu.
TargetName=dist\DeepFocus_Setup.exe
FriendlyName=DeepFocus Installer
AppLaunched=cmd.exe /c powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\DeepFocus_Installer.ps1" && del "%TEMP%\DeepFocus_Installer.ps1"
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=
[Strings]
AppName=DeepFocus
FILE0="install.ps1"
FILE1="DeepFocus_Data.zip"
"@

$sedPath = Join-Path $TempDir "installer.sed"
$sedContent | Out-File -FilePath $sedPath -Encoding ASCII

# Copy files needed for IExpress
Copy-Item $installerScriptPath (Join-Path $TempDir "install.ps1") -Force
Copy-Item $archivePath (Join-Path $TempDir "DeepFocus_Data.zip") -Force

# Create a simpler installer script that extracts and installs
$simpleInstallScript = @"
`$ErrorActionPreference = "Stop"

# Check admin
`$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not `$isAdmin) {
    `$scriptPath = `$MyInvocation.MyCommand.Path
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File ``"`$scriptPath``"" -Wait
    exit
}

Write-Host "Installing DeepFocus..." -ForegroundColor Cyan

# Extract archive from same directory as this script
`$scriptDir = Split-Path -Parent `$MyInvocation.MyCommand.Path
`$archivePath = Join-Path `$scriptDir "DeepFocus_Data.zip"
`$installDir = "`$env:ProgramFiles\DeepFocus"

if (Test-Path `$installDir) {
    Remove-Item `$installDir -Recurse -Force
}
New-Item -ItemType Directory -Path `$installDir -Force | Out-Null

Expand-Archive -Path `$archivePath -DestinationPath `$installDir -Force

# Create shortcuts
`$exePath = Join-Path `$installDir "deepfocus.exe"
`$shell = New-Object -ComObject WScript.Shell

`$desktopShortcut = `$shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "DeepFocus.lnk"))
`$desktopShortcut.TargetPath = `$exePath
`$desktopShortcut.WorkingDirectory = `$installDir
`$desktopShortcut.Description = "DeepFocus - Social Media Blocker"
`$desktopShortcut.Save()

`$startMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) "DeepFocus"
if (-not (Test-Path `$startMenuDir)) {
    New-Item -ItemType Directory -Path `$startMenuDir -Force | Out-Null
}

`$startShortcut = `$shell.CreateShortcut((Join-Path `$startMenuDir "DeepFocus.lnk"))
`$startShortcut.TargetPath = `$exePath
`$startShortcut.WorkingDirectory = `$installDir
`$startShortcut.Description = "DeepFocus - Social Media Blocker"
`$startShortcut.Save()

# Registry
`$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DeepFocus"
New-Item -Path `$regPath -Force -ErrorAction SilentlyContinue | Out-Null
Set-ItemProperty -Path `$regPath -Name "DisplayName" -Value "DeepFocus - Social Media Blocker" -Force
Set-ItemProperty -Path `$regPath -Name "DisplayIcon" -Value `$exePath -Force
Set-ItemProperty -Path `$regPath -Name "Publisher" -Value "NeuroBrain" -Force
Set-ItemProperty -Path `$regPath -Name "DisplayVersion" -Value "0.1.0" -Force

Write-Host "Installation complete!" -ForegroundColor Green
"@

$simpleInstallScript | Out-File -FilePath (Join-Path $TempDir "install.ps1") -Encoding UTF8 -Force

# Try to use IExpress
$iexpressPath = Join-Path ${env:SystemRoot} "System32\iexpress.exe"
if (Test-Path $iexpressPath) {
    Write-Host "  Found IExpress, creating installer..." -ForegroundColor Cyan
    
    # Update SED with correct file paths
    $sedContent = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=0
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%AppName% Installation
DisplayLicense=
FinishMessage=DeepFocus has been installed successfully!
TargetName=dist\DeepFocus_Setup.exe
FriendlyName=DeepFocus Installer
AppLaunched=cmd.exe /c powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\DeepFocus_Installer.ps1"
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=$TempDir
[Strings]
AppName=DeepFocus
FILE0="install.ps1"
FILE1="DeepFocus_Data.zip"
"@
    $sedContent | Out-File -FilePath $sedPath -Encoding ASCII -Force
    
    # Run IExpress silently
    $iexpressArgs = "/N /Q `"$sedPath`""
    Start-Process -FilePath $iexpressPath -ArgumentList $iexpressArgs -Wait -NoNewWindow
    
    if (Test-Path "dist\DeepFocus_Setup.exe") {
        Write-Host "  Single EXE installer created: dist\DeepFocus_Setup.exe" -ForegroundColor Green
    } else {
        Write-Host "  IExpress failed, using PowerShell installer instead" -ForegroundColor Yellow
    }
} else {
    Write-Host "  IExpress not found, using PowerShell installer" -ForegroundColor Yellow
}

# Cleanup
Remove-Item $TempDir -Recurse -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installer Created Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "dist\DeepFocus_Setup.exe") {
    $fileInfo = Get-Item "dist\DeepFocus_Setup.exe"
    $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Host "Single EXE Installer: dist\DeepFocus_Setup.exe ($fileSizeMB MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "This is a single executable installer file that users can:" -ForegroundColor Yellow
    Write-Host "  1. Double-click to run" -ForegroundColor White
    Write-Host "  2. It will request admin privileges" -ForegroundColor White
    Write-Host "  3. Install DeepFocus to Program Files" -ForegroundColor White
    Write-Host "  4. Create Desktop and Start Menu shortcuts" -ForegroundColor White
} else {
    Write-Host "PowerShell Installer: dist\DeepFocus_Installer.ps1" -ForegroundColor Green
    Write-Host ""
    Write-Host "This is a self-contained installer. Users can:" -ForegroundColor Yellow
    Write-Host "  1. Right-click and 'Run with PowerShell'" -ForegroundColor White
    Write-Host "  2. Or rename to .bat and double-click" -ForegroundColor White
}

Write-Host ""