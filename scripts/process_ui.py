"""将 ui/ 下的 .ui 文件编译为 _ui.py 到 ui/gen/"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UI_DIR = PROJECT_ROOT / "ui"
OUT_DIR = PROJECT_ROOT / "ui" / "gen"


def main():
    ui_files = sorted(UI_DIR.glob("*.ui"))
    if not ui_files:
        print("❌ 未找到 .ui 文件")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for ui in ui_files:
        py_path = OUT_DIR / f"{ui.stem}_ui.py"
        cmd = f"pyside6-uic '{ui}' -o '{py_path}'"
        ret = os.system(cmd)
        if ret == 0:
            print(f"  ✓ {py_path.relative_to(PROJECT_ROOT)}")
        else:
            print(f"  ✗ 编译失败: {ui.name}")

    print(f"\n✅ 完成，共 {len(ui_files)} 个文件")


if __name__ == "__main__":
    main()
