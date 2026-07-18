#!/usr/bin/env bash
# ========================================
#  可靠性工具 Linux 构建脚本
# ========================================
# 用法：
#   ./packaging/build.sh                 # Release 模式
#   ./packaging/build.sh --debug         # 调试模式（显示控制台）
#   ./packaging/build.sh --novenv        # 跳过 venv
#   ./packaging/build.sh --nosplash      # 跳过启动画面
#   ./packaging/build.sh --onedir        # 打包为目录
# ========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ── 参数解析 ──
DEBUG=""
NO_VENV=""
NO_SPLASH=""
ONE_DIR=""

for arg in "$@"; do
    case "$arg" in
        --debug)    DEBUG="1" ;;
        --novenv)   NO_VENV="1" ;;
        --nosplash) NO_SPLASH="1" ;;
        --onedir)   ONE_DIR="1" ;;
    esac
done

echo "========================================"
echo "   可靠性工具 Linux 构建脚本"
echo "========================================"

# ── Step 1. 找 Python ──
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[ERROR] 未找到 Python，请安装 Python 3.11+"
    exit 1
fi

PY_VER="$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "[OK] Python: $PY_VER ($(which $PYTHON))"

# ── Step 2. 虚拟环境 ──
VENV_DIR="$SCRIPT_DIR/venv"

if [ -z "$NO_VENV" ]; then
    if [ ! -d "$VENV_DIR" ]; then
        echo "[..] 创建虚拟环境..."
        $PYTHON -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    PYTHON="$VENV_DIR/bin/python"
    echo "[OK] 虚拟环境: $PYTHON"
else
    echo "[!] 跳过 venv，使用当前环境"
fi

# ── Step 3. 安装依赖 ──
echo "[..] 安装依赖..."
"$PYTHON" -m pip install -r "$PROJECT_ROOT/requirements.txt" -q 2>/dev/null || true
"$PYTHON" -m pip install pyinstaller -q 2>/dev/null || true
echo "[OK] 依赖安装完成"

# ── Step 4. 读取版本号 ──
VERSION="unknown"
VERSION_FILE="$PROJECT_ROOT/VERSION"
if [ -f "$VERSION_FILE" ]; then
    VERSION="$(cat "$VERSION_FILE" | tr -d '[:space:]')"
fi

# ── Step 5. 清理旧构建 ──
OUTPUT_DIR="$PROJECT_ROOT/dist"
if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"
fi

# ── Step 6. 执行 PyInstaller ──
OUTPUT_MODE="--onefile"
if [ -n "$ONE_DIR" ]; then
    OUTPUT_MODE="--onedir"
fi

WINDOW_MODE="--windowed"
LABEL="Release"
if [ -n "$DEBUG" ]; then
    WINDOW_MODE=""
    LABEL="调试模式"
fi

echo "[..] 开始打包 ($LABEL)..."

cd "$PROJECT_ROOT"
"$PYTHON" -m PyInstaller \
    --clean \
    --noconfirm \
    --name "reliability-tool-v$VERSION" \
    "$OUTPUT_MODE" \
    $WINDOW_MODE \
    --add-data "VERSION:." \
    --add-data "config:config" \
    --add-data "TDDB_template.xlsx:." \
    --add-data "huawei_logo.png:." \
    --add-data "icon.png:." \
    --add-data "splash.jpg:." \
    --add-data "ui/gen/formula_images:ui/gen/formula_images" \
    --icon "icon.png" \
    --contents-directory "_internal" \
    --hidden-import "scipy" \
    --collect-all "PySide6" \
    --hidden-import "PySide6" \
    --hidden-import "PySide6.QtCore" \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "PySide6.QtGui" \
    --hidden-import "core.ft_cache" \
    --hidden-import "core.FT_file_parser" \
    --hidden-import "core.data_merge" \
    --hidden-import "core.plotting" \
    --hidden-import "core.draw_excel" \
    --hidden-import "xlsxwriter" \
    --hidden-import "core.compare" \
    --hidden-import "core.unit_converter" \
    --hidden-import "core.test_item_patterns" \
    --hidden-import "ui.gen.mainWindow" \
    --hidden-import "ui.gen.FTDataAnalisys" \
    --hidden-import "ui.gen.FTDataAnalisysConfig" \
    --hidden-import "ui.gen.config_manager" \
    --hidden-import "ui.gen.logger" \
    --hidden-import "ui.gen.tddb_tool" \
    --hidden-import "ui.gen.progress_worker" \
    --hidden-import "ui.gen.conflict_dialog" \
    --hidden-import "SplashModule" \
    "app.py"

if [ $? -ne 0 ]; then
    echo "[ERROR] PyInstaller 打包失败"
    exit 1
fi

# ── Step 7. 收尾清理 ──
DIST_DIR="$PROJECT_ROOT/dist/reliability-tool-v$VERSION"
if [ -d "$DIST_DIR" ]; then
    find "$DIST_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$DIST_DIR" -name "*.pyc" -delete 2>/dev/null || true

    EXE_FILE="$DIST_DIR/reliability-tool-v$VERSION"
    if [ -f "$EXE_FILE" ]; then
        SIZE="$(du -h "$EXE_FILE" | cut -f1)"
        echo "========================================"
        echo "  构建成功!"
        echo "  输出: $DIST_DIR"
        echo "  exe:  reliability-tool-v$VERSION"
        echo "  大小: $SIZE"
        echo "========================================"
    fi
fi
