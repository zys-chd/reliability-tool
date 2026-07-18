<#
.SYNOPSIS
    可靠性工具 Windows 一键构建脚本
.DESCRIPTION
    创建虚拟环境 → 安装依赖 → 使用 PyInstaller 打包为单个 exe。
    用法：
    .\packaging\build.ps1                  # Release 模式
    .\packaging\build.ps1 -Debug            # 调试模式（显示控制台）
    .\packaging\build.ps1 -NoVenv           # 跳过 venv，使用当前环境
    .\packaging\build.ps1 -OneDir           # 打包为目录（调试用）
#>

param(
    [switch]$Debug,
    [switch]$NoVenv,
    [switch]$OneDir
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   可靠性工具 Windows 构建脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── Step 1. 找 Python ──
$python = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command "python3" -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "[ERROR] 未找到 Python，请安装 Python 3.11+" -ForegroundColor Red
    exit 1
}
$pyVer = & $python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "[OK] Python: $pyVer ($($python.Source))" -ForegroundColor Green

# ── Step 2. 虚拟环境 ──
$venvPath = Join-Path $ScriptDir "venv_win"
$pip = $null

if (-not $NoVenv) {
    if (-not (Test-Path $venvPath)) {
        Write-Host "[..] 创建虚拟环境..." -ForegroundColor Yellow
        & $python.Source -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] venv 创建失败" -ForegroundColor Red
            exit 1
        }
    }
    $python = Get-Command (Join-Path $venvPath "Scripts\python.exe") -ErrorAction SilentlyContinue
    $pip = Get-Command (Join-Path $venvPath "Scripts\pip.exe") -ErrorAction SilentlyContinue
    if (-not $python -or -not $pip) {
        Write-Host "[ERROR] venv 中未找到 python/pip" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] 虚拟环境: $($python.Source)" -ForegroundColor Green
} else {
    $pip = Get-Command "pip" -ErrorAction SilentlyContinue
    Write-Host "[!] 跳过 venv，使用当前环境" -ForegroundColor Yellow
}

# ── Step 3. 安装依赖 ──
Write-Host "[..] 安装依赖..." -ForegroundColor Yellow
$reqFile = Join-Path $ProjectRoot "requirements.txt"
& $pip.Source install -r $reqFile 2>&1 | Out-Null
& $pip.Source install pyinstaller 2>&1 | Out-Null
Write-Host "[OK] 依赖安装完成" -ForegroundColor Green

# ── Step 4. 读取版本号 ──
$versionFile = Join-Path $ProjectRoot "VERSION"
$version = "unknown"
if (Test-Path $versionFile) {
    $version = (Get-Content $versionFile -Raw).Trim()
}

# ── Step 5. 清理旧构建 ──
$outputDir = Join-Path $ProjectRoot "dist"
if (Test-Path $outputDir) {
    Remove-Item -Recurse -Force $outputDir -ErrorAction SilentlyContinue
}

# ── Step 6. 执行 PyInstaller ──
$outputMode = if ($OneDir) { "--onedir" } else { "--onefile" }
$windowMode = if ($Debug) { "" } else { "--windowed" }
$consoleLabel = if ($Debug) { "调试模式" } else { "Release 模式" }

Write-Host "[..] 开始打包 ($consoleLabel)..." -ForegroundColor Yellow

Push-Location $ProjectRoot
try {
    & $python.Source -m PyInstaller `
        --clean `
        --noconfirm `
        --name "reliability-tool-v$version" `
        $outputMode `
        $windowMode `
        --add-data "VERSION;." `
        --add-data "config;config" `
        --add-data "TDDB_template.xlsx;." `
        --add-data "huawei_logo.png;." `
        --add-data "icon.ico;." `
        --add-data "icon.png;." `
        --add-data "splash.jpg;." `
        --add-data "ui/gen/formula_images;ui/gen/formula_images" `
        --icon "icon.ico" `
        --contents-directory "_internal" `
        --hidden-import "scipy" `
        --collect-all "PySide6" `
        --hidden-import "core.ft_cache" `
        --hidden-import "core.FT_file_parser" `
        --hidden-import "core.data_merge" `
        --hidden-import "core.plotting" `
        --hidden-import "core.draw_excel" `
        --hidden-import "xlsxwriter" `
        --hidden-import "core.compare" `
        --hidden-import "core.unit_converter" `
        --hidden-import "core.test_item_patterns" `
        --hidden-import "ui.gen.mainWindow" `
        --hidden-import "ui.gen.FTDataAnalisys" `
        --hidden-import "ui.gen.FTDataAnalisysConfig" `
        --hidden-import "ui.gen.config_manager" `
        --hidden-import "ui.gen.logger" `
        --hidden-import "ui.gen.tddb_tool" `
        --hidden-import "ui.gen.progress_worker" `
        --hidden-import "ui.gen.conflict_dialog" `
        --hidden-import "SplashModule" `
        "app.py"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] PyInstaller 打包失败" -ForegroundColor Red
        exit 1
    }
}
finally {
    Pop-Location
}

# ── Step 7. 收尾清理 ──
$distExeDir = Join-Path $ProjectRoot "dist/reliability-tool-v$version"
if (Test-Path $distExeDir) {
    # 清理 __pycache__ 和 .pyc
    Get-ChildItem -Recurse -Directory -Path $distExeDir -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -File -Path $distExeDir -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-Child-item -Recurse -File -Path "$distExeDir\_internal" -Filter "*.pdb" | Remove-Item -Force -ErrorAction SilentlyContinue

    $exeFile = Join-Path $distExeDir "reliability-tool-v$version.exe"
    if (Test-Path $exeFile) {
        $size = (Get-Item $exeFile).Length / 1MB
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  构建成功!" -ForegroundColor Green
        Write-Host "  输出: $distExeDir" -ForegroundColor Green
        Write-Host "  exe:  reliability-tool-v$version.exe" -ForegroundColor Green
        Write-Host "  大小: $([math]::Round($size, 1)) MB" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
    }
}
