<#
.SYNOPSIS
    可靠性工具 Windows 一键打包脚本
.DESCRIPTION
    创建虚拟环境 → 安装依赖 → 使用 PyInstaller 打包为独立 exe。
    只打包必要模块，排除测试/文档/开发工具等无用依赖。

    用法：
        .\packaging\build.ps1                 # 默认打包（Release）
        .\packaging\build.ps1 -Debug           # 调试模式（保留控制台窗口）
        .\packaging\build.ps1 -NoVenv          # 跳过 venv 创建，使用当前环境
#>

param(
    [switch]$Debug,
    [switch]$NoVenv,
    # [switch]$OneFile,
    [switch]$NoSplash,
    [switch]$OneDir
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   可靠性工具  Windows 打包脚本           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── 1. 检查 Python ─────────────────────────────────────────────
$python = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command "python3" -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "[错误] 未找到 Python，请安装 Python 3.11+（建议 Python 3.12）" -ForegroundColor Red
    Write-Host "       下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
$pyVersion = & $python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host "[?] Python: $pyVersion ($($python.Source))" -ForegroundColor Green

# ─── 2. 虚拟环境 ────────────────────────────────────────────────
$venvPath = Join-Path $ScriptDir "venv"
$pip = $null

if (-not $NoVenv) {
    if (-not (Test-Path $venvPath)) {
        Write-Host "[...] 创建虚拟环境: $venvPath" -ForegroundColor Yellow
        & $python.Source -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[错误] venv 创建失败" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[?] 使用已有虚拟环境" -ForegroundColor Green
    }

    $pip = Get-Command (Join-Path $venvPath "Scripts\pip.exe") -ErrorAction SilentlyContinue
    $pythonVenv = Get-Command (Join-Path $venvPath "Scripts\python.exe") -ErrorAction SilentlyContinue
    if (-not $pip -or -not $pythonVenv) {
        Write-Host "[错误] 虚拟环境中未找到 pip/python" -ForegroundColor Red
        exit 1
    }
    Write-Host "[?] 虚拟环境 Python: $($pythonVenv.Source)" -ForegroundColor Green
} else {
    $pip = Get-Command "pip" -ErrorAction SilentlyContinue
    $pythonVenv = $python
    if (-not $pip) {
        Write-Host "[错误] 未找到 pip" -ForegroundColor Red
        exit 1
    }
    Write-Host "[!] 跳过 venv，使用当前环境" -ForegroundColor Yellow
}

# ─── 3. 安装依赖 ────────────────────────────────────────────────
Write-Host ""
Write-Host "── 安装运行时依赖 ──" -ForegroundColor Cyan
$reqFile = Join-Path $ProjectRoot "requirements.txt"
& $pip.Source install -r $reqFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] 部分依赖安装失败，继续尝试..." -ForegroundColor Yellow
}

Write-Host "── 安装打包工具 ──" -ForegroundColor Cyan
& $pip.Source install pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] PyInstaller 安装失败" -ForegroundColor Red
    exit 1
}
Write-Host "[?] 依赖安装完成" -ForegroundColor Green

# ─── 4. 打包 ────────────────────────────────────────────────────
Write-Host ""
Write-Host "── 开始打包 ──" -ForegroundColor Cyan

# 构建额外排除列表（在 spec 基础上再补充）
$excludes = @(
    # "tkinter",
    # "matplotlib.tests",
    # "numpy.testing",
    # "pandas.tests",
    # "PIL.ImageShow",
    # "IPython",
    "jupyter",
    "jupyter_client",
    "jupyter_core",
    "nbformat",
    "nbconvert",
    "notebook",
    "pytest"
    # "unittest",
    # "setuptools",
    # "pip",
    # "wheel"
    # "pkg_resources",
    # "distutils",
    # "idlelib",
    # "turtledemo",
    # "test",
    # "email.mime",
    # "http.server",
    # "socketserver",
    # "xmlrpc",
    # "pdb",
    # "profile",
    # "cProfile",
    # "doctest",
    # "pydoc",
    # "smtpd",
    # "telnetlib",
    # "webbrowser",
    # "sqlite3",
    # "asyncio",
    # "ensurepip",
    # "venv",
    # "_tkinter",
    # "PIL",
    # "cffi",
    # "cryptography",
    # "zmq",
    # "pygments",
    # "jsonschema",
    # "requests",
    # "urllib3",
    # "idna",
    # "certifi",
    # "charset_normalizer",
    # "cycler",
    # "fonttools",
    # "kiwisolver",
    # "pyparsing",
    # "tornado",
    # "defusedxml",
    # "tinycss2",
    # "lxml",
    # "MarkupSafe",
    # "mistune",
    # "packaging",
    # "prometheus_client",
    # "send2trash",
    # "terminado",
    # "websocket",
    # "anyio",
    # "sniffio",
    # "h11",
    # "outcome",
    # "numpy.core.multiarray_tests",
    # "scipy.spatial",
    # "scipy.special",
    # "scipy.signal",
    # "scipy.io",
    # "scipy.sparse",
    # "scipy.integrate",
    # "scipy.interpolate",
    # "scipy.cluster",
    # "scipy.ndimage",
    # "scipy.odr",
    # "scipy.fftpack"
)

# 从 VERSION 文件读取版本用于输出目录命名
$versionFile = Join-Path $ProjectRoot "VERSION"
$version = "unknown"
if (Test-Path $versionFile) {
    $version = (Get-Content $versionFile -Raw).Trim()
}

$outputDir = Join-Path $ProjectRoot "dist"
if (Test-Path $outputDir) {
    Write-Host "[...] 清理旧的 dist 目录..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $outputDir -ErrorAction SilentlyContinue
}

# 切换到项目根目录执行 pyinstaller
Push-Location $ProjectRoot
try {
    # 生成 spec 中使用的排除参数
    $excludeArgs = $excludes | ForEach-Object { "--exclude-module", $_ }
    $splashArg = if ($NoSplash) { "" } else { "--splash icon.png" }
    $outputDirArg = if ($OneDir) { " --onedir " } else { " --onefile " }

    if ($Debug) {
        Write-Host "[!] 调试模式：显示控制台窗口（方便查看 print/log）" -ForegroundColor Yellow
        & $pythonVenv.Source -m PyInstaller `
            --clean `
            --noconfirm `
            --name "reliability-tool-v$version" `
            $outputDirArg `
            --add-data "VERSION;." `
            --add-data "ui/gen/formula_images;ui/gen/formula_images" `
            --icon "" `
            --contents-directory "_internal" `
            $excludeArgs `
            "app.py"

        if ($LASTEXITCODE -ne 0) {
            Write-Host "[错误] PyInstaller 打包失败" -ForegroundColor Red
            exit 1
        }
    } else {
        & $pythonVenv.Source -m PyInstaller `
            --clean `
            --noconfirm `
            --name "reliability-tool-v$version" `
            $outputDirArg `
            --windowed `
            --add-data "VERSION;." `
            --add-data "ui/gen/formula_images;ui/gen/formula_images" `
            --add-data "icon.ico;." `
            --add-data "icon.png;." `
            --icon "icon.ico" `
            $splashArg `
            --contents-directory "_internal" `
            --hidden-import "scipy" `
            --hidden-import "PySide6.QtWebEngineWidgets" `
            --hidden-import "PySide6.QtWebEngineCore" `
            --hidden-import "PySide6.QtWebChannel" `
            --hidden-import "core.data_merge" `
            --hidden-import "core.plotting" `
            --hidden-import "core.webengine_check" `
            --hidden-import "core.path_utils" `
            --hidden-import "core.open_file" `
            --hidden-import "core.file_parser" `
            --hidden-import "core.column_mapper" `
            --hidden-import "core.format_detector" `
            --hidden-import "core.unit_converter" `
            --hidden-import "core.test_item_patterns" `
            --hidden-import "core.compare" `
            --hidden-import "core.data_merge" `
            --hidden-import "core.ut_translator" `
            --hidden-import "core.draw_excel" `
            --hidden-import "core.tddb.models" `
            --hidden-import "core.tddb.weibull_fitter" `
            --hidden-import "core.tddb.area_scaling" `
            --hidden-import "core.tddb.confidence" `
            --hidden-import "core.tddb.beta_diagnostics" `
            --hidden-import "core.tddb.test_data" `
            --hidden-import "ui.gen.mainWindow" `
            --hidden-import "ui.gen.mainWindow_ui" `
            --hidden-import "ui.gen.FTDataAnalisys" `
            --hidden-import "ui.gen.FTDataAnalisys_ui" `
            --hidden-import "ui.gen.FTDataAnalisysConfig" `
            --hidden-import "ui.gen.FTDataAnalisysConfig_ui" `
            --hidden-import "ui.gen.config_manager" `
            --hidden-import "ui.gen.config_schemas" `
            --hidden-import "ui.gen.logger" `
            --hidden-import "ui.gen.tddb_tool" `
            --hidden-import "ui.gen.TDDBTool_ui" `
            --hidden-import "ui.gen.TDDB_custom_draw_ui" `
            --hidden-import "ui.gen.conflict_dialog" `
            --hidden-import "ui.gen.cross_conflict_dialog" `
            --hidden-import "ui.gen.test_item_selector" `
            --hidden-import "ui.gen.formula_dialog" `
            --hidden-import "ui.gen.progress_worker" `
            $excludeArgs `
            "app.py"

        if ($LASTEXITCODE -ne 0) {
            Write-Host "[错误] PyInstaller 打包失败" -ForegroundColor Red
            exit 1
        }
    }
}
finally {
    Pop-Location
}

# ─── 5. 确保 VERSION 文件在 dist 中 ─────────────────────────────
$distExeDir = Join-Path $ProjectRoot "dist/reliability-tool-v$version"
if (Test-Path $distExeDir) {
    # copy VERSION if not already bundled
    if (-not (Test-Path (Join-Path $distExeDir "VERSION"))) {
        Copy-Item $versionFile (Join-Path $distExeDir "_internal\VERSION")
    }

    # ─── 6. 清理无用文件 ────────────────────────────────────────
    Write-Host ""
    Write-Host "── 清理打包产物中的无用文件 ──" -ForegroundColor Cyan

    # 删除 __pycache__
    Get-ChildItem -Recurse -Directory -Path $distExeDir -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # 删除 .pyc 文件
    Get-ChildItem -Recurse -File -Path $distExeDir -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue

    # 删除 pdb 符号文件
    Get-ChildItem -Recurse -File -Path "$distExeDir\_internal" -Filter "*.pdb" | Remove-Item -Force -ErrorAction SilentlyContinue

    # 删除 .lib 文件（静态库，运行时不需要）
    Get-ChildItem -Recurse -File -Path "$distExeDir\_internal" -Filter "*.lib" | Remove-Item -Force -ErrorAction SilentlyContinue

    Write-Host "[?] 清理完成" -ForegroundColor Green
}

# ─── 7. 结果汇总 ────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              打包完成！                    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if (Test-Path $distExeDir) {
    $exeFile = Join-Path $distExeDir "reliability-tool-v$version.exe"
    if (Test-Path $exeFile) {
        $size = (Get-Item $exeFile).Length / 1MB
        $totalSize = (Get-ChildItem -Recurse $distExeDir | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "  输出目录: $distExeDir" -ForegroundColor Green
        Write-Host "  主程序:   reliability-tool-v$version.exe" -ForegroundColor Green
        Write-Host "  主程序大小: {0:N1} MB" -f $size -ForegroundColor Green
        Write-Host "  总大小:   {0:N1} MB" -f $totalSize -ForegroundColor Green
        Write-Host ""
        Write-Host "  提示: 分发时复制整个 reliability-tool-v$version 文件夹即可" -ForegroundColor Yellow
        Write-Host "       用户电脑上无需安装 Python 或 Qt" -ForegroundColor Yellow
    } else {
        Write-Host "[警告] 未找到 exe 文件，请检查 dist 目录" -ForegroundColor Yellow
    }
} else {
    Write-Host "[警告] dist 目录不存在，打包可能出错" -ForegroundColor Yellow
}
