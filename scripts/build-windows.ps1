# SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
# SPDX-License-Identifier: GPL-3.0-or-later
<#
.SYNOPSIS
Configure and build Emulator for Windows x64 (Qt GUI emulator-fx.exe and emulator-fx-cli.exe).

.DESCRIPTION
Needs: Visual Studio 2022 with "Desktop development with C++", CMake >= 3.31, Ninja,
Vulkan SDK (glslangValidator on PATH; tools/windows/install-vulkan-sdk.ps1 installs it),
Python 3, git. Qt is downloaded by the build (YUZU_USE_BUNDLED_QT) unless -QtDir names
an installed Qt 6 (msvc2022_64).

.EXAMPLE
pwsh scripts/build-windows.ps1                 # Release build into build\windows
pwsh scripts/build-windows.ps1 -Tests          # also build and run the unit tests
pwsh scripts/build-windows.ps1 -Clean -Tests   # from an empty build directory
#>
param(
    [string]$BuildDir = "build\windows",
    [ValidateSet("Release", "RelWithDebInfo", "Debug")][string]$Config = "Release",
    [string]$QtDir = "",
    [switch]$Tests,
    [switch]$Clean,
    [switch]$Clang,
    [int]$Jobs = 0
)
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if (-not $env:VCINSTALLDIR) { & "$root\tools\windows\load-msvc-env.ps1" }
if (-not (Get-Command glslangValidator -ErrorAction SilentlyContinue)) {
    if ($env:VULKAN_SDK) { $env:PATH = "$env:VULKAN_SDK\Bin;$env:PATH" }
}
if (-not (Get-Command glslangValidator -ErrorAction SilentlyContinue)) {
    throw "glslangValidator not found: install the Vulkan SDK (tools/windows/install-vulkan-sdk.ps1, as admin)"
}

if ($Clean -and (Test-Path $BuildDir)) { Remove-Item -Recurse -Force $BuildDir }

$testFlag = if ($Tests) { "ON" } else { "OFF" }
$flags = @(
    "-S", ".", "-B", $BuildDir, "-G", "Ninja",
    "-DCMAKE_BUILD_TYPE=$Config",
    "-DYUZU_TESTS=$testFlag",
    "-DBUILD_TESTING=$testFlag",
    "-DYUZU_CMD=ON",
    "-DYUZU_USE_BUNDLED_SDL3=ON"
)
if ($QtDir) { $flags += @("-DYUZU_USE_BUNDLED_QT=OFF", "-DCMAKE_PREFIX_PATH=$QtDir") }
if ($Clang) { $flags += @("-DCMAKE_C_COMPILER=clang-cl", "-DCMAKE_CXX_COMPILER=clang-cl") }
if (Get-Command sccache -ErrorAction SilentlyContinue) {
    $flags += @("-DCMAKE_C_COMPILER_LAUNCHER=sccache", "-DCMAKE_CXX_COMPILER_LAUNCHER=sccache")
}

& cmake @flags
if ($LASTEXITCODE) { throw "configure failed" }

$targets = @("yuzu", "yuzu-cmd")
if ($Tests) { $targets += @("tests", "update_checker_tests") }
$par = if ($Jobs -gt 0) { @("--parallel", $Jobs) } else { @("--parallel") }
& cmake --build $BuildDir --target @targets @par
if ($LASTEXITCODE) { throw "build failed" }

Write-Host "built: $BuildDir\bin\emulator-fx.exe, $BuildDir\bin\emulator-fx-cli.exe"

if ($Tests) {
    & ctest --test-dir $BuildDir --output-on-failure
    if ($LASTEXITCODE) { throw "tests failed" }
    # The Ocarina of Time regression tests, listed separately so a sync report can quote them.
    & "$BuildDir\bin\tests.exe" "[oot]" --reporter compact
    if ($LASTEXITCODE) { throw "Ocarina tests failed" }
}
