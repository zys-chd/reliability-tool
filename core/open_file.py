"""跨平台打开文件 — 用系统默认程序打开"""

import os
import subprocess
import sys
from pathlib import Path


def open_file(path: str | Path):
    """打开文件/目录，使用系统默认程序（跨平台）"""
    path_obj = Path(path).resolve()
    path_str = str(path_obj)
    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {path_str}")
    try:
        if sys.platform == "win32":
            try:
                os.startfile(path_str)
            except AttributeError:
                # os.startfile 在某些 Windows Python 环境中可能缺失
                subprocess.run(["cmd", "/c", "start", "", path_str], check=True)
        elif sys.platform == "darwin":
            subprocess.run(["open", path_str], check=True)
        else:  # linux / other unix
            subprocess.run(["xdg-open", path_str], check=True)
    except Exception as e:
        raise RuntimeError(f"打开文件失败: {path_str}\n{e}")
