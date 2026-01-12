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
    $buildResult = & flet build windows 2>&1
    $buildOutput = $buildResult | Out-String
    
    # Check if build completed (even if install step fails)
    if ($buildOutput -match "Building Windows application.*?(\d+\.\d+s)") {
        Write-Host "Build compilation completed!" -ForegroundColor Green
    }
    
    # Show any errors but continue
    if ($buildOutput -match "error MSB3073") {
        Write-Host "Warning: Install step failed (this is expected - we'll fix it)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error during flet build: $_" -ForegroundColor Red
    Write-Host "Build output saved for debugging." -ForegroundColor Yellow
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

# Check if Python runtime files exist and copy if missing
$pythonDlls = Get-ChildItem "$ReleaseDir\DLLs" -Filter "python*.dll" -ErrorAction SilentlyContinue
if ($pythonDlls.Count -eq 0) {
    Write-Host "  Warning: Python DLLs not found - checking embedded Python..." -ForegroundColor Yellow
    
    # Ensure DLLs directory exists
    if (-not (Test-Path "$ReleaseDir\DLLs")) {
        New-Item -ItemType Directory -Path "$ReleaseDir\DLLs" -Force | Out-Null
    }
    
    $foundDlls = @()
    
    # Check serious_python build output for Python DLLs
    $seriousPythonDir = "build\flutter\build\windows\x64\plugins\serious_python_windows"
    if (Test-Path $seriousPythonDir) {
        $pythonDllsFromSerious = Get-ChildItem $seriousPythonDir -Recurse -Filter "python*.dll" -ErrorAction SilentlyContinue
        if ($pythonDllsFromSerious) {
            Write-Host "  Found Python DLLs in serious_python build, copying..." -ForegroundColor Cyan
            foreach ($dll in $pythonDllsFromSerious) {
                Copy-Item -Path $dll.FullName -Destination "$ReleaseDir\DLLs\" -Force
                $foundDlls += $dll.Name
            }
        }
    }
    
    # Check site-packages for embedded Python
    $embeddedPython = Get-ChildItem "$ReleaseDir\site-packages" -Recurse -Filter "python*.dll" -ErrorAction SilentlyContinue
    if ($embeddedPython) {
        Write-Host "  Found Python DLLs in site-packages, copying..." -ForegroundColor Cyan
        foreach ($dll in $embeddedPython) {
            $dest = Join-Path "$ReleaseDir\DLLs" $dll.Name
            if (-not (Test-Path $dest)) {
                Copy-Item -Path $dll.FullName -Destination "$ReleaseDir\DLLs\" -Force
                $foundDlls += $dll.Name
            }
        }
    }
    
    if ($foundDlls.Count -gt 0) {
        Write-Host "  Copied $($foundDlls.Count) Python DLL(s): $($foundDlls -join ', ')" -ForegroundColor Green
    } else {
        Write-Host "  Warning: Python DLLs not found automatically" -ForegroundColor Yellow
        Write-Host "  serious_python should embed Python runtime during build" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Python DLLs found: $($pythonDlls.Count) file(s)" -ForegroundColor Green
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
