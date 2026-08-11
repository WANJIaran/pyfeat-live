param(
    [string]$UvVersion = "0.10.11"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

foreach ($command in @("node", "npm", "pnpm", "cargo")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $command. See WINDOWS_HANDOFF.md."
    }
}

$uvTarget = Join-Path $PSScriptRoot "vendor\uv\uv-x86_64-pc-windows-msvc.exe"
if (-not (Test-Path $uvTarget)) {
    $uvDir = Split-Path $uvTarget
    New-Item -ItemType Directory -Force $uvDir | Out-Null
    $tempDir = Join-Path $env:TEMP "facial-affect-index-uv"
    New-Item -ItemType Directory -Force $tempDir | Out-Null
    $archive = Join-Path $tempDir "uv.zip"
    $unpacked = Join-Path $tempDir "unpacked"
    Invoke-WebRequest `
        "https://github.com/astral-sh/uv/releases/download/$UvVersion/uv-x86_64-pc-windows-msvc.zip" `
        -OutFile $archive
    Expand-Archive $archive -DestinationPath $unpacked -Force
    $uv = Get-ChildItem $unpacked -Recurse -Filter uv.exe | Select-Object -First 1
    if (-not $uv) { throw "uv.exe was not found in the downloaded archive." }
    Copy-Item $uv.FullName $uvTarget -Force
}

Push-Location (Join-Path $PSScriptRoot "tauri")
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw "npm ci failed with exit code $LASTEXITCODE" }
    npm run tauri:build -- --bundles nsis --config "src-tauri/tauri.windows.local.conf.json"
    if ($LASTEXITCODE -ne 0) { throw "Tauri build failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

$installerDir = Join-Path $PSScriptRoot "tauri\src-tauri\target\release\bundle\nsis"
if (-not (Test-Path $installerDir)) {
    throw "Build returned without creating the NSIS directory: $installerDir"
}
Write-Host "Build completed. Installer directory: $installerDir" -ForegroundColor Green
Get-ChildItem $installerDir -Filter *.exe
