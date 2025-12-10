#requires -Version 5.1
<#
.SYNOPSIS
  RadioPotato Git pre-push helper.

.DESCRIPTION
  執行診斷腳本與 PyInstaller 打包，確保推送前流程一致。
  可直接透過 `.git\hooks\pre-push` 呼叫，亦可於手動打包時執行：

      powershell -ExecutionPolicy Bypass -File tools\prepush.ps1

.NOTES
  若需跳過測試，可加入 `-SkipTests` 參數。
#>

[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Write-Host "==> RadioPotato pre-push starting at $root" -ForegroundColor Cyan

# 決定 Python 執行檔
$pythonCandidates = @(
    "$env:VIRTUAL_ENV\Scripts\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python38\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    (Get-Command python -ErrorAction SilentlyContinue)?.Source,
    (Get-Command py -ErrorAction SilentlyContinue)?.Source
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

if (-not $pythonCandidates) {
    throw "找不到 Python 執行檔，請先安裝 Python 或啟動虛擬環境。"
}

$pythonExe = $pythonCandidates[0]
Write-Host "使用 Python: $pythonExe"

# 執行診斷
$diagnosticArgs = @("tools/run_diagnostics.py")
if ($SkipTests) { $diagnosticArgs += "--skip-tests" }

Write-Host "==> Running diagnostics..." -ForegroundColor Yellow
$diag = Start-Process -FilePath $pythonExe `
    -ArgumentList $diagnosticArgs `
    -WorkingDirectory $root `
    -NoNewWindow -Wait -PassThru

if ($diag.ExitCode -ne 0) {
    throw "診斷失敗（ExitCode=$($diag.ExitCode)），請修正後再次執行。"
}

if (-not $SkipBuild) {
    if (-not (Test-Path "$root/build.spec")) {
        throw "找不到 build.spec，無法執行打包。"
    }

    Write-Host "==> Running PyInstaller build..." -ForegroundColor Yellow
    $pyinstallerCmd = (Get-Command pyinstaller -ErrorAction SilentlyContinue)?.Source
    if ($pyinstallerCmd) {
        $build = Start-Process -FilePath $pyinstallerCmd `
            -ArgumentList "build.spec" `
            -WorkingDirectory $root `
            -NoNewWindow -Wait -PassThru
    }
    else {
        $build = Start-Process -FilePath $pythonExe `
            -ArgumentList @("-m", "PyInstaller", "build.spec") `
            -WorkingDirectory $root `
            -NoNewWindow -Wait -PassThru
    }

    if ($build.ExitCode -ne 0) {
        throw "PyInstaller 打包失敗（ExitCode=$($build.ExitCode)）。"
    }
}
else {
    Write-Host "==> 跳過 PyInstaller 打包" -ForegroundColor DarkYellow
}

Write-Host "==> Pre-push checks passed." -ForegroundColor Green
exit 0

