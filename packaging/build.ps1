<#
.SYNOPSIS
    �ɿ��Թ��� Windows һ������ű�
.DESCRIPTION
    �������⻷�� �� ��װ���� �� ʹ�� PyInstaller ���Ϊ���� exe��
    ֻ�����Ҫģ�飬�ų�����/�ĵ�/�������ߵ�����������

    �÷���
        .\packaging\build.ps1                 # Ĭ�ϴ����Release��
        .\packaging\build.ps1 -Debug           # ����ģʽ����������̨���ڣ�
        .\packaging\build.ps1 -NoVenv          # ���� venv ������ʹ�õ�ǰ����
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

Write-Host "�X�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�[" -ForegroundColor Cyan
Write-Host "�U   �ɿ��Թ���  Windows ����ű�           �U" -ForegroundColor Cyan
Write-Host "�^�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�a" -ForegroundColor Cyan
Write-Host ""

# ������ 1. ��� Python ������������������������������������������������������������������������������������������
$python = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command "python3" -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "[����] δ�ҵ� Python���밲װ Python 3.11+������ Python 3.12��" -ForegroundColor Red
    Write-Host "       ���ص�ַ: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
$pyVersion = & $python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host "[?] Python: $pyVersion ($($python.Source))" -ForegroundColor Green

# ������ 2. ���⻷�� ������������������������������������������������������������������������������������������������
$venvPath = Join-Path $ScriptDir "venv"
$pip = $null

if (-not $NoVenv) {
    if (-not (Test-Path $venvPath)) {
        Write-Host "[...] �������⻷��: $venvPath" -ForegroundColor Yellow
        & $python.Source -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[����] venv ����ʧ��" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[?] ʹ���������⻷��" -ForegroundColor Green
    }

    $pip = Get-Command (Join-Path $venvPath "Scripts\pip.exe") -ErrorAction SilentlyContinue
    $pythonVenv = Get-Command (Join-Path $venvPath "Scripts\python.exe") -ErrorAction SilentlyContinue
    if (-not $pip -or -not $pythonVenv) {
        Write-Host "[����] ���⻷����δ�ҵ� pip/python" -ForegroundColor Red
        exit 1
    }
    Write-Host "[?] ���⻷�� Python: $($pythonVenv.Source)" -ForegroundColor Green
} else {
    $pip = Get-Command "pip" -ErrorAction SilentlyContinue
    $pythonVenv = $python
    if (-not $pip) {
        Write-Host "[����] δ�ҵ� pip" -ForegroundColor Red
        exit 1
    }
    Write-Host "[!] ���� venv��ʹ�õ�ǰ����" -ForegroundColor Yellow
}

# ������ 3. ��װ���� ������������������������������������������������������������������������������������������������
Write-Host ""
Write-Host "���� ��װ����ʱ���� ����" -ForegroundColor Cyan
$reqFile = Join-Path $ProjectRoot "requirements.txt"
& $pip.Source install -r $reqFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "[����] ����������װʧ�ܣ���������..." -ForegroundColor Yellow
}

Write-Host "���� ��װ������� ����" -ForegroundColor Cyan
& $pip.Source install pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "[����] PyInstaller ��װʧ��" -ForegroundColor Red
    exit 1
}
Write-Host "[?] ������װ���" -ForegroundColor Green

# ������ 4. ��� ��������������������������������������������������������������������������������������������������������
Write-Host ""
Write-Host "���� ��ʼ��� ����" -ForegroundColor Cyan

# ���������ų��б����� spec �������ٲ��䣩
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

# �� VERSION �ļ���ȡ�汾�������Ŀ¼����
$versionFile = Join-Path $ProjectRoot "VERSION"
$version = "unknown"
if (Test-Path $versionFile) {
    $version = (Get-Content $versionFile -Raw).Trim()
}

$outputDir = Join-Path $ProjectRoot "dist"
if (Test-Path $outputDir) {
    Write-Host "[...] �����ɵ� dist Ŀ¼..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $outputDir -ErrorAction SilentlyContinue
}

# �л�����Ŀ��Ŀ¼ִ�� pyinstaller
Push-Location $ProjectRoot
try {
    # ���� spec ��ʹ�õ��ų�����
    $excludeArgs = $excludes | ForEach-Object { "--exclude-module", $_ }
    $splashArg = if ($NoSplash) { "" } else { "--splash icon.png" }
    $outputDirArg = if ($OneDir) { " --onedir " } else { " --onefile " }

    if ($Debug) {
        Write-Host "[!] 调试模式，显示控制台窗口，方便查看 print/log。" -ForegroundColor Yellow
        & $pythonVenv.Source -m PyInstaller `
            --clean `
            --noconfirm `
            --name "reliability-tool-v$version" `
            $outputDirArg `
            --add-data "VERSION;." `
            --add-data "config;config" `
            --add-data "ui/gen/formula_images;ui/gen/formula_images" `
            --add-data "TDDB_template.xlsx;." `
            --add-data "huawei_logo.png;." `
            --add-data "icon.png;." `
            --icon "" `
            --contents-directory "_internal" `
            $excludeArgs `
            "app.py"

        if ($LASTEXITCODE -ne 0) {
            Write-Host "[����] PyInstaller ���ʧ��" -ForegroundColor Red
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
            --add-data "config;config" `
            --add-data "ui/gen/formula_images;ui/gen/formula_images" `
            --add-data "TDDB_template.xlsx;." `
            --add-data "huawei_logo.png;." `
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
            Write-Host "[����] PyInstaller ���ʧ��" -ForegroundColor Red
            exit 1
        }
    }
}
finally {
    Pop-Location
}

# ������ 5. ȷ�� VERSION �ļ��� dist �� ����������������������������������������������������������
$distExeDir = Join-Path $ProjectRoot "dist/reliability-tool-v$version"
if (Test-Path $distExeDir) {
    # copy VERSION if not already bundled
    if (-not (Test-Path (Join-Path $distExeDir "VERSION"))) {
        Copy-Item $versionFile (Join-Path $distExeDir "_internal\VERSION")
    }

    # ������ 6. ���������ļ� ��������������������������������������������������������������������������������
    Write-Host ""
    Write-Host "���� ������������е������ļ� ����" -ForegroundColor Cyan

    # ɾ�� __pycache__
    Get-ChildItem -Recurse -Directory -Path $distExeDir -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # ɾ�� .pyc �ļ�
    Get-ChildItem -Recurse -File -Path $distExeDir -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue

    # ɾ�� pdb �����ļ�
    Get-ChildItem -Recurse -File -Path "$distExeDir\_internal" -Filter "*.pdb" | Remove-Item -Force -ErrorAction SilentlyContinue

    # ɾ�� .lib �ļ�����̬�⣬����ʱ����Ҫ��
    Get-ChildItem -Recurse -File -Path "$distExeDir\_internal" -Filter "*.lib" | Remove-Item -Force -ErrorAction SilentlyContinue

    Write-Host "[?] �������" -ForegroundColor Green
}

# ������ 7. ������� ������������������������������������������������������������������������������������������������
Write-Host ""
Write-Host "�X�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�[" -ForegroundColor Cyan
Write-Host "�U              �����ɣ�                    �U" -ForegroundColor Cyan
Write-Host "�^�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�T�a" -ForegroundColor Cyan
Write-Host ""

if (Test-Path $distExeDir) {
    $exeFile = Join-Path $distExeDir "reliability-tool-v$version.exe"
    if (Test-Path $exeFile) {
        $size = (Get-Item $exeFile).Length / 1MB
        $totalSize = (Get-ChildItem -Recurse $distExeDir | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "  ���Ŀ¼: $distExeDir" -ForegroundColor Green
        Write-Host "  ������:   reliability-tool-v$version.exe" -ForegroundColor Green
        Write-Host "  �������С: {0:N1} MB" -f $size -ForegroundColor Green
        Write-Host "  �ܴ�С:   {0:N1} MB" -f $totalSize -ForegroundColor Green
        Write-Host ""
        Write-Host "  ��ʾ: �ַ�ʱ�������� reliability-tool-v$version �ļ��м���" -ForegroundColor Yellow
        Write-Host "       �û����������谲װ Python �� Qt" -ForegroundColor Yellow
    } else {
        Write-Host "[����] δ�ҵ� exe �ļ������� dist Ŀ¼" -ForegroundColor Yellow
    }
} else {
    Write-Host "[����] dist Ŀ¼�����ڣ�������ܳ���" -ForegroundColor Yellow
}
