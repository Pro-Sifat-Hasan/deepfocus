# Automated Windows Build Script for DeepFocus
# This script handles the complete build process and ensures all dependencies are included

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DeepFocus - Automated Windows Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Configuration
$BuildDir = "build\flutter\build\windows\x64"
$ReleaseDir = "$BuildDir\runner\Release"
$PluginsDir = "$BuildDir\plugins"
$OutputDir = "dist\DeepFocus"

Write-Host "[1/4] Starting Flet build process..." -ForegroundColor Yellow
Write-Host ""

# Step 1: Run Flet build
try {
    Write-Host "Running: flet build windows" -ForegroundColor Cyan
    $buildResult = & flet build windows 2>&1
    $buildOutput = $buildResult | Out-String
    
    # Check if build completed (even if install step fails)
    if ($buildOutput -match "Building Windows application.*?(\d+\.\d+s)") {
        Write-Host "Build compilation completed!" -ForegroundColor Green
    }
    
    # Show any errors but continue (install step failures are expected)
    if ($buildOutput -match "error MSB3073") {
        Write-Host "Note: Install step failed (this is okay - we'll copy files manually)" -ForegroundColor Yellow
    }
    
    # Check if build actually succeeded
    if (-not (Test-Path $ReleaseDir)) {
        Write-Host "ERROR: Release directory not found. Build may have failed completely." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error during flet build: $_" -ForegroundColor Red
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
    if (-not (Test-Path $ReleaseDir)) {
        exit 1
    }
}

Write-Host ""
Write-Host "[2/4] Copying plugin DLLs..." -ForegroundColor Yellow

# Step 2: Copy plugin DLLs
if (Test-Path $PluginsDir) {
    $pluginDlls = Get-ChildItem -Path $PluginsDir -Recurse -Filter "*plugin*.dll" -ErrorAction SilentlyContinue
    
    if ($pluginDlls.Count -gt 0) {
        if (-not (Test-Path $ReleaseDir)) {
            New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
        }
        
        $copied = 0
        foreach ($dll in $pluginDlls) {
            $destPath = Join-Path $ReleaseDir $dll.Name
            try {
                Copy-Item -Path $dll.FullName -Destination $destPath -Force
                $copied++
            } catch {
                Write-Host "  Failed to copy $($dll.Name): $_" -ForegroundColor Red
            }
        }
        Write-Host "  Copied $copied plugin DLL(s)" -ForegroundColor Green
    } else {
        Write-Host "  No plugin DLLs found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Plugins directory not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/4] Verifying required files..." -ForegroundColor Yellow

# Step 3: Verify all required files exist
$requiredFiles = @(
    "$ReleaseDir\deepfocus.exe",
    "$ReleaseDir\flutter_windows.dll"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "  ERROR: Missing required files:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "    - $file" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Build may have failed. Please check the build output above." -ForegroundColor Red
    exit 1
}

Write-Host "  All required files found" -ForegroundColor Green

# Step 3b: Copy Python runtime from serious_python (if CopyPythonDLLs target didn't run)
$pythonDlls = Get-ChildItem "$ReleaseDir\DLLs" -Filter "python*.dll" -ErrorAction SilentlyContinue
if ($pythonDlls.Count -eq 0) {
    Write-Host "  Python DLLs not found in Release/DLLs - searching for Python runtime..." -ForegroundColor Yellow
    
    # Ensure DLLs and Lib directories exist
    if (-not (Test-Path "$ReleaseDir\DLLs")) {
        New-Item -ItemType Directory -Path "$ReleaseDir\DLLs" -Force | Out-Null
    }
    if (-not (Test-Path "$ReleaseDir\Lib")) {
        New-Item -ItemType Directory -Path "$ReleaseDir\Lib" -Force | Out-Null
    }
    
    $pythonFound = $false
    $pythonDllsSrc = $null
    $python3DllSrc = $null
    
    # Search locations in order of priority:
    # 1. serious_python plugin directory
    $searchPaths = @(
        "build\flutter\build\windows\x64\plugins\serious_python_windows\python",
        "build\flutter\build\windows\x64\plugins\serious_python_windows",
        "$env:LOCALAPPDATA\flet\flutter\build\windows\x64\plugins\serious_python_windows\python",
        "$env:USERPROFILE\.flet\flutter\build\windows\x64\plugins\serious_python_windows\python"
    )
    
    # Also check Release directory itself (sometimes DLLs are copied there directly)
    $releasePythonDlls = Get-ChildItem "$ReleaseDir" -Filter "python*.dll" -ErrorAction SilentlyContinue
    if ($releasePythonDlls.Count -gt 0) {
        Write-Host "  Found Python DLLs in Release directory - moving to DLLs folder..." -ForegroundColor Cyan
        foreach ($dll in $releasePythonDlls) {
            Move-Item -Path $dll.FullName -Destination "$ReleaseDir\DLLs\" -Force
            Write-Host "    Moved $($dll.Name) to DLLs folder" -ForegroundColor Green
        }
        $pythonFound = $true
    }
    
    # Search in serious_python directories
    if (-not $pythonFound) {
        foreach ($searchPath in $searchPaths) {
            if (Test-Path $searchPath) {
                Write-Host "  Searching in: $searchPath" -ForegroundColor Gray
                
                # Check if python312.dll or python3.dll exists directly
                $python312Path = Join-Path $searchPath "python312.dll"
                $python3Path = Join-Path $searchPath "python3.dll"
                
                # Also search recursively for python*.dll files
                $foundDlls = Get-ChildItem -Path $searchPath -Recurse -Filter "python*.dll" -ErrorAction SilentlyContinue
                
                if ($foundDlls.Count -gt 0 -or (Test-Path $python312Path) -or (Test-Path $python3Path)) {
                    Write-Host "  Found Python runtime in: $searchPath" -ForegroundColor Cyan
                    
                    # Copy main Python DLLs
                    if (Test-Path $python312Path) {
                        Copy-Item -Path $python312Path -Destination "$ReleaseDir\DLLs\" -Force
                        Write-Host "    Copied python312.dll" -ForegroundColor Green
                        $pythonFound = $true
                    }
                    if (Test-Path $python3Path) {
                        Copy-Item -Path $python3Path -Destination "$ReleaseDir\DLLs\" -Force
                        Write-Host "    Copied python3.dll" -ForegroundColor Green
                        $pythonFound = $true
                    }
                    
                    # Copy any other Python DLLs found recursively
                    foreach ($dll in $foundDlls) {
                        if ($dll.Name -match "^(python312|python3)\.dll$") {
                            $destPath = Join-Path "$ReleaseDir\DLLs" $dll.Name
                            if (-not (Test-Path $destPath)) {
                                Copy-Item -Path $dll.FullName -Destination "$ReleaseDir\DLLs\" -Force
                                Write-Host "    Copied $($dll.Name)" -ForegroundColor Green
                                $pythonFound = $true
                            }
                        }
                    }
                    
                    # Copy DLLs directory contents
                    $pythonDllsDir = Join-Path $searchPath "DLLs"
                    if (Test-Path $pythonDllsDir) {
                        Copy-Item -Path "$pythonDllsDir\*" -Destination "$ReleaseDir\DLLs\" -Recurse -Force
                        Write-Host "    Copied Python DLLs directory" -ForegroundColor Green
                    }
                    
                    # Copy Lib directory (Python standard library) only if not already present
                    $pythonLibDir = Join-Path $searchPath "Lib"
                    if (Test-Path $pythonLibDir -and -not (Test-Path "$ReleaseDir\Lib\site-packages")) {
                        Copy-Item -Path "$pythonLibDir\*" -Destination "$ReleaseDir\Lib\" -Recurse -Force -ErrorAction SilentlyContinue
                        Write-Host "    Copied Python Lib directory" -ForegroundColor Green
                    }
                    
                    break
                }
            }
        }
    }
    
    # Final check: try to find Python DLLs from system Python installation as fallback
    # Also search more broadly for python312.dll
    if (-not $pythonFound) {
        Write-Host "  Attempting to find Python DLLs from system installation..." -ForegroundColor Yellow
        
        # First, check if python312.dll specifically is missing
        $python312Exists = Test-Path "$ReleaseDir\DLLs\python312.dll"
        
        # Search in common Python installation locations
        $systemPythonPaths = @(
            "$env:ProgramFiles\Python312",
            "$env:ProgramFiles\Python311", 
            "$env:ProgramFiles\Python310",
            "${env:ProgramFiles(x86)}\Python312",
            "${env:ProgramFiles(x86)}\Python311",
            "${env:ProgramFiles(x86)}\Python310",
            "$env:LOCALAPPDATA\Programs\Python\Python312",
            "$env:LOCALAPPDATA\Programs\Python\Python311",
            "$env:LOCALAPPDATA\Programs\Python\Python310",
            "$env:USERPROFILE\AppData\Local\Programs\Python\Python312",
            "$env:USERPROFILE\AppData\Local\Programs\Python\Python311",
            "$env:USERPROFILE\AppData\Local\Programs\Python\Python310"
        )
        
        # Also search recursively in Program Files for Python directories
        $searchPaths = @()
        foreach ($basePath in @("$env:ProgramFiles", "${env:ProgramFiles(x86)}", "$env:LOCALAPPDATA\Programs")) {
            if (Test-Path $basePath) {
                $pyDirs = Get-ChildItem -Path $basePath -Directory -Filter "Python*" -ErrorAction SilentlyContinue
                foreach ($pyDir in $pyDirs) {
                    if ($pyDir.Name -match "Python312|Python3\.12") {
                        $searchPaths += $pyDir.FullName
                    }
                }
            }
        }
        $systemPythonPaths = $searchPaths + $systemPythonPaths
        
        foreach ($pyPath in $systemPythonPaths) {
            if (Test-Path $pyPath) {
                # Prioritize python312.dll
                $sysPython312 = Join-Path $pyPath "python312.dll"
                $sysPython3 = Join-Path $pyPath "python3.dll"
                
                # Also check in DLLs subdirectory
                $sysPython312Dlls = Join-Path $pyPath "DLLs\python312.dll"
                $sysPython3Dlls = Join-Path $pyPath "DLLs\python3.dll"
                
                # Copy python312.dll first (most important)
                if (Test-Path $sysPython312) {
                    Copy-Item -Path $sysPython312 -Destination "$ReleaseDir\DLLs\" -Force
                    Write-Host "    Copied python312.dll from: $pyPath" -ForegroundColor Green
                    $python312Exists = $true
                    $pythonFound = $true
                } elseif (Test-Path $sysPython312Dlls) {
                    Copy-Item -Path $sysPython312Dlls -Destination "$ReleaseDir\DLLs\" -Force
                    Write-Host "    Copied python312.dll from: $pyPath\DLLs" -ForegroundColor Green
                    $python312Exists = $true
                    $pythonFound = $true
                }
                
                # Copy python3.dll as well if not already present
                if (-not (Test-Path "$ReleaseDir\DLLs\python3.dll")) {
                    if (Test-Path $sysPython3) {
                        Copy-Item -Path $sysPython3 -Destination "$ReleaseDir\DLLs\" -Force
                        Write-Host "    Copied python3.dll from: $pyPath" -ForegroundColor Green
                        $pythonFound = $true
                    } elseif (Test-Path $sysPython3Dlls) {
                        Copy-Item -Path $sysPython3Dlls -Destination "$ReleaseDir\DLLs\" -Force
                        Write-Host "    Copied python3.dll from: $pyPath\DLLs" -ForegroundColor Green
                        $pythonFound = $true
                    }
                }
                
                if ($python312Exists) { break }
            }
        }
    }
    
    # Final verification: Check if python312.dll is present
    $python312Final = Test-Path "$ReleaseDir\DLLs\python312.dll"
    $python3Final = Test-Path "$ReleaseDir\DLLs\python3.dll"
    
    if (-not $python312Final) {
        Write-Host "  ERROR: python312.dll was not found!" -ForegroundColor Red
        Write-Host "  The application will NOT work without python312.dll" -ForegroundColor Red
        Write-Host "  Please ensure Python 3.12 is installed or serious_python downloads it during build" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  You can manually copy python312.dll:" -ForegroundColor Yellow
        Write-Host "    1. Find python312.dll in your Python 3.12 installation" -ForegroundColor White
        Write-Host "    2. Copy it to: $ReleaseDir\DLLs\" -ForegroundColor White
        exit 1
    } else {
        # Verify DLLs are now present
        $finalCheck = Get-ChildItem "$ReleaseDir\DLLs" -Filter "python*.dll" -ErrorAction SilentlyContinue
        $dllList = $finalCheck | ForEach-Object { $_.Name } | Sort-Object
        Write-Host "  Python DLLs successfully copied: $($finalCheck.Count) file(s)" -ForegroundColor Green
        foreach ($dll in $dllList) {
            Write-Host "    - $dll" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  Python DLLs already present: $($pythonDlls.Count) file(s)" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/4] Creating distribution package..." -ForegroundColor Yellow

# Step 4: Create distribution folder
if (Test-Path $OutputDir) {
    Remove-Item $OutputDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

# Copy entire Release directory
Write-Host "  Copying all files to distribution folder..." -ForegroundColor Cyan
Copy-Item -Path "$ReleaseDir\*" -Destination $OutputDir -Recurse -Force

Write-Host "  Distribution package created at: $OutputDir" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Creating single-file installer..." -ForegroundColor Yellow

# Step 5: Create single-file installer
try {
    # Create zip archive of distribution folder
    $archivePath = Join-Path $env:TEMP "DeepFocus_Data_$([Guid]::NewGuid().ToString().Substring(0,8)).zip"
    Compress-Archive -Path "$OutputDir\*" -DestinationPath $archivePath -Force
    
    # Read archive as Base64
    $archiveBytes = [System.IO.File]::ReadAllBytes($archivePath)
    $archiveBase64 = [Convert]::ToBase64String($archiveBytes)
    
    # Create self-contained installer script (avoid nested here-strings)
    $installerScriptHeader = @'
# DeepFocus Installer - Self-Contained
# This installer contains all files embedded

$ErrorActionPreference = "Stop"

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" -Wait
    exit
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DeepFocus - Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Extract embedded archive
$base64Archive = @"
'@
    
    $installerScriptFooter = @'
"@

$tempArchive = Join-Path $env:TEMP "DeepFocus_$([Guid]::NewGuid().ToString().Substring(0,8)).zip"
$archiveBytes = [Convert]::FromBase64String($base64Archive)
[System.IO.File]::WriteAllBytes($tempArchive, $archiveBytes)

# Install location
$installDir = "$env:ProgramFiles\DeepFocus"
Write-Host "Installing to: $installDir" -ForegroundColor Cyan

if (Test-Path $installDir) {
    Write-Host "Removing existing installation..." -ForegroundColor Yellow
    Remove-Item $installDir -Recurse -Force
}
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

# Extract files
Write-Host "Extracting files..." -ForegroundColor Yellow
Expand-Archive -Path $tempArchive -DestinationPath $installDir -Force
Remove-Item $tempArchive -Force

# Create shortcuts
Write-Host "Creating shortcuts..." -ForegroundColor Yellow
$startMenu = [Environment]::GetFolderPath("Programs")
$startMenuDir = Join-Path $startMenu "DeepFocus"
if (-not (Test-Path $startMenuDir)) {
    New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
}

$exePath = Join-Path $installDir "deepfocus.exe"
$desktop = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell

$desktopShortcut = $shell.CreateShortcut((Join-Path $desktop "DeepFocus.lnk"))
$desktopShortcut.TargetPath = $exePath
$desktopShortcut.WorkingDirectory = $installDir
$desktopShortcut.Description = "DeepFocus - Social Media Blocker"
$desktopShortcut.Save()

$startShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "DeepFocus.lnk"))
$startShortcut.TargetPath = $exePath
$startShortcut.WorkingDirectory = $installDir
$startShortcut.Description = "DeepFocus - Social Media Blocker"
$startShortcut.Save()

# Add to Add/Remove Programs
$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DeepFocus"
New-Item -Path $regPath -Force -ErrorAction SilentlyContinue | Out-Null
Set-ItemProperty -Path $regPath -Name "DisplayName" -Value "DeepFocus - Social Media Blocker" -Force
Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value $exePath -Force
Set-ItemProperty -Path $regPath -Name "Publisher" -Value "NeuroBrain" -Force
Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value "0.1.0" -Force
Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "powershell.exe -Command `"Remove-Item -Path '$installDir' -Recurse -Force`"" -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "DeepFocus has been installed successfully!" -ForegroundColor Green
Write-Host "Location: $installDir" -ForegroundColor Cyan
Write-Host "You can now launch DeepFocus from Desktop or Start Menu." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
'@
    
    # Combine header + Base64 archive + footer
    $installerScript = $installerScriptHeader + "`r`n" + $archiveBase64 + "`r`n" + $installerScriptFooter

    # Save installer script
    $installerPath = "dist\DeepFocus_Installer.ps1"
    $installerScript | Out-File -FilePath $installerPath -Encoding UTF8
    
    # Cleanup temp archive
    Remove-Item $archivePath -Force -ErrorAction SilentlyContinue
    
    Write-Host "  Single-file installer created: $installerPath" -ForegroundColor Green
    
    # Create a simple batch wrapper for easy execution
    $batchWrapper = @"
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0DeepFocus_Installer.ps1"
"@
    $batchPath = "dist\DeepFocus_Installer.bat"
    $batchWrapper | Out-File -FilePath $batchPath -Encoding ASCII
    
    Write-Host "  Batch wrapper created: $batchPath" -ForegroundColor Green
    
} catch {
    Write-Host "  WARNING: Failed to create installer: $_" -ForegroundColor Yellow
    Write-Host "  Distribution folder is ready at: $OutputDir" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Distribution folder: $((Resolve-Path $OutputDir).Path)" -ForegroundColor Cyan
if (Test-Path "dist\DeepFocus_Installer.ps1") {
    $installerSize = [math]::Round((Get-Item "dist\DeepFocus_Installer.ps1").Length / 1MB, 2)
    Write-Host ""
    Write-Host "Single-file installer created!" -ForegroundColor Green
    Write-Host "  File: dist\DeepFocus_Installer.ps1 ($installerSize MB)" -ForegroundColor Cyan
    Write-Host "  Wrapper: dist\DeepFocus_Installer.bat (double-click to run)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To distribute:" -ForegroundColor Yellow
    Write-Host "  Share the file: dist\DeepFocus_Installer.ps1" -ForegroundColor White
    Write-Host "  Users can:" -ForegroundColor White
    Write-Host "    - Right-click and 'Run with PowerShell', OR" -ForegroundColor Gray
    Write-Host "    - Double-click DeepFocus_Installer.bat" -ForegroundColor Gray
    Write-Host "  The installer will request admin privileges and install DeepFocus" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "To share your app:" -ForegroundColor Yellow
    Write-Host "  1. Zip the entire '$OutputDir' folder" -ForegroundColor White
    Write-Host "  2. Share the zip file" -ForegroundColor White
    Write-Host "  3. Recipients extract and run deepfocus.exe from the folder" -ForegroundColor White
}
Write-Host ""
Write-Host "To test the app:" -ForegroundColor Yellow
Write-Host "  cd $OutputDir" -ForegroundColor White
Write-Host "  .\deepfocus.exe" -ForegroundColor White
Write-Host ""
