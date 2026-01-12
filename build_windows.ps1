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
    Write-Host "  Python DLLs not found in Release/DLLs - copying from serious_python..." -ForegroundColor Yellow
    
    # Ensure DLLs and Lib directories exist
    if (-not (Test-Path "$ReleaseDir\DLLs")) {
        New-Item -ItemType Directory -Path "$ReleaseDir\DLLs" -Force | Out-Null
    }
    if (-not (Test-Path "$ReleaseDir\Lib")) {
        New-Item -ItemType Directory -Path "$ReleaseDir\Lib" -Force | Out-Null
    }
    
    # Find serious_python's extracted Python package
    $seriousPythonBuildDir = "build\flutter\build\windows\x64\plugins\serious_python_windows"
    $pythonPackageDir = Join-Path $seriousPythonBuildDir "python"
    
    if (Test-Path $pythonPackageDir) {
        Write-Host "  Found Python package in serious_python build directory" -ForegroundColor Cyan
        
        # Copy Python DLLs
        $pythonDllsSrc = Join-Path $pythonPackageDir "python312.dll"
        $python3DllSrc = Join-Path $pythonPackageDir "python3.dll"
        
        if (Test-Path $pythonDllsSrc) {
            Copy-Item -Path $pythonDllsSrc -Destination "$ReleaseDir\DLLs\" -Force
            Write-Host "    Copied python312.dll" -ForegroundColor Green
        }
        if (Test-Path $python3DllSrc) {
            Copy-Item -Path $python3DllSrc -Destination "$ReleaseDir\DLLs\" -Force
            Write-Host "    Copied python3.dll" -ForegroundColor Green
        }
        
        # Copy DLLs directory contents
        $pythonDllsDir = Join-Path $pythonPackageDir "DLLs"
        if (Test-Path $pythonDllsDir) {
            Copy-Item -Path "$pythonDllsDir\*" -Destination "$ReleaseDir\DLLs\" -Recurse -Force
            Write-Host "    Copied Python DLLs directory" -ForegroundColor Green
        }
        
        # Copy Lib directory (Python standard library)
        $pythonLibDir = Join-Path $pythonPackageDir "Lib"
        if (Test-Path $pythonLibDir) {
            if (-not (Test-Path "$ReleaseDir\Lib")) {
                Copy-Item -Path $pythonLibDir -Destination "$ReleaseDir\Lib" -Recurse -Force
                Write-Host "    Copied Python Lib directory" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  Warning: Python package directory not found" -ForegroundColor Yellow
        Write-Host "  Location checked: $pythonPackageDir" -ForegroundColor Gray
        Write-Host "  serious_python should download Python during build" -ForegroundColor Yellow
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

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Distribution folder: $((Resolve-Path $OutputDir).Path)" -ForegroundColor Cyan
Write-Host ""
Write-Host "To share your app:" -ForegroundColor Yellow
Write-Host "  1. The entire '$OutputDir' folder contains everything needed" -ForegroundColor White
Write-Host "  2. Zip the folder and share it" -ForegroundColor White
Write-Host "  3. Recipients extract and run deepfocus.exe from the folder" -ForegroundColor White
Write-Host "     (All DLLs and dependencies are included in the folder)" -ForegroundColor Gray
Write-Host ""
Write-Host "To test the app:" -ForegroundColor Yellow
Write-Host "  cd $OutputDir" -ForegroundColor White
Write-Host "  .\deepfocus.exe" -ForegroundColor White
Write-Host ""
Write-Host "Note: The exe must stay with its DLL and data folders to work." -ForegroundColor Cyan
Write-Host "      Share the entire folder, not just the exe file." -ForegroundColor Cyan
Write-Host ""
