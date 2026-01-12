# Script to copy plugin DLLs to Release directory after build
# This fixes the issue where install step fails but DLLs need to be copied

$ErrorActionPreference = "Stop"

$BuildDir = Join-Path $PSScriptRoot "build\flutter\build\windows\x64"
$ReleaseDir = Join-Path $BuildDir "runner\Release"
$PluginsDir = Join-Path $BuildDir "plugins"

Write-Host "Copying plugin DLLs to Release directory..." -ForegroundColor Cyan

if (-not (Test-Path $ReleaseDir)) {
    Write-Host "Release directory not found: $ReleaseDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $PluginsDir)) {
    Write-Host "Plugins directory not found: $PluginsDir" -ForegroundColor Red
    exit 1
}

# Find all plugin DLLs in the plugins directory
$pluginDlls = Get-ChildItem -Path $PluginsDir -Recurse -Filter "*plugin*.dll" -ErrorAction SilentlyContinue

if ($pluginDlls.Count -eq 0) {
    Write-Host "No plugin DLLs found in: $PluginsDir" -ForegroundColor Yellow
    exit 0
}

$copied = 0
foreach ($dll in $pluginDlls) {
    $destPath = Join-Path $ReleaseDir $dll.Name
    try {
        Copy-Item -Path $dll.FullName -Destination $destPath -Force
        Write-Host "  Copied: $($dll.Name)" -ForegroundColor Green
        $copied++
    } catch {
        Write-Host "  Failed to copy $($dll.Name): $_" -ForegroundColor Red
    }
}

Write-Host "`nCopied $copied plugin DLL(s) to Release directory." -ForegroundColor Green
Write-Host "Release directory: $ReleaseDir" -ForegroundColor Cyan
