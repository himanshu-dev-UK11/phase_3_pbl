$ErrorActionPreference = "Stop"

$CoreDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $CoreDirectory

$Compiler = Get-Command x86_64-w64-mingw32-gcc -ErrorAction SilentlyContinue
if (-not $Compiler) {
    $CodeBlocksCompiler = "C:\Program Files\CodeBlocks\MinGW\bin\x86_64-w64-mingw32-gcc.exe"
    if (Test-Path $CodeBlocksCompiler) {
        $Compiler = $CodeBlocksCompiler
    }
}

if (-not $Compiler) {
    Write-Host "64-bit gcc not found. Install a 64-bit MinGW toolchain first."
    exit 1
}

& $Compiler -shared -O2 -Wall -Wextra -static-libgcc -o monitor_core.dll monitor_core.c -lm

if ($LASTEXITCODE -ne 0) {
    Write-Host "C build failed."
    exit 1
}

Write-Host "Done. monitor_core.dll created."
