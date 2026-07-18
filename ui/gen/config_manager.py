#!/usr/bin/env python3
"""
配置管理器 - 基于 TOML，多 section，自动补默认 key，记录活跃 section。

使用方式：
    schema = {"key1": {"default": "val", "type": str},
              "key2": {"default": 0,    "type": int}}
    cm = ConfigManager("config/group.toml", schema)
    cm.load()
    cm.get("key1")        # 当前活跃 section 的值
    cm.set("key1", "new")
    cm.save()
"""

import os
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any


def _format_toml_value(val: Any) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, str):
        # TOML 字符串必须转义控制字符
        escaped = val.replace("\\", "\\\\")
        escaped = escaped.replace('"', '\\"')
        escaped = escaped.replace("\n", "\\n")
        escaped = escaped.replace("\r", "\\r")
        escaped = escaped.replace("\t", "\\t")
        return f'"{escaped}"'
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, dict):
        items = []
        for k, v in val.items():
            # TOML key 如果不是纯字母数字下划线就需要引号
            key = str(k)
            if not key.isidentifier():
                key = f'"{key}"'
            items.append(f'{key} = {_format_toml_value(v)}')
        return "{" + ", ".join(items) + "}"
    if isinstance(val, (list, tuple)):
        items = [_format_toml_value(v) for v in val]
        return "[" + ", ".join(items) + "]"
    if val is None:
        return '""'
    return str(val)


def _serialize_toml(data: dict) -> str:
    """将 dict 序列化为 TOML 格式，支持 [[array_of_tables]] 和普通 [section]"""
    lines = []
    for section_name, section_data in data.items():
        if isinstance(section_data, list) and all(isinstance(x, dict) for x in section_data):
            # [[array_of_tables]] — 如 signatures
            for item in section_data:
                lines.append(f"[[{section_name}]]")
                for k, v in item.items():
                    if v is not None and v != "" and v != [] and v != {}:
                        lines.append(f'{k} = {_format_toml_value(v)}')
                lines.append("")
        elif isinstance(section_data, dict):
            # 普通 [section]
            lines.append(f"[{section_name}]")
            for k, v in section_data.items():
                if v is not None and v != "" and v != [] and v != {}:
                    lines.append(f'{k} = {_format_toml_value(v)}')
            lines.append("")
        else:
            # 顶层键值（极少数情况）
            if section_data is not None:
                lines.append(f'{section_name} = {_format_toml_value(section_data)}')
    return "\n".join(lines)


class SchemaError(Exception):
    pass


class ConfigManager:
    """管理一个 TOML 配置文件，包含多个 section + meta 追踪活跃 section"""

    def __init__(self, filepath: str | Path, schema: dict,
                 logger=None, default_section: str = "default"):
        self.filepath = Path(filepath)
        self.schema = schema          # {key: {"default": ..., "type": ..., "label": ...}}
        self.default_section = default_section
        self._logger = logger
        self._data: dict[str, dict] = {}       # section_name → {key: value}
        self._active_section: str = default_section
        self._dirty = False

    # ── 公开属性 ──────────────────────────────────────────────

    @property
    def active_section(self) -> str:
        return self._active_section

    @property
    def sections(self) -> list[str]:
        return [k for k in self._data if k != "meta"]

    @property
    def active(self) -> dict:
        """当前活跃 section 的完整配置 dict"""
        return dict(self._data.get(self._active_section, {}))

    # ── 加载与保存 ────────────────────────────────────────────

    def load(self):
        """加载 TOML 文件，自动补全缺失 key"""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        if not self.filepath.exists():
            self._log(f"配置文件不存在，新建: {self.filepath}")
            self._data = {}
            self._ensure_default()
            self._ensure_schema()
            self.save()
            return

        try:
            raw = self.filepath.read_bytes()
            self._data = tomllib.loads(raw.decode("utf-8"))
        except Exception as e:
            self._log(f"配置文件解析失败: {e}，将备份后重建", "warning")
            # 备份损坏的文件
            backup_path = self.filepath.with_suffix(".toml.bak")
            import shutil
            shutil.copy2(self.filepath, backup_path)
            self._log(f"已备份到: {backup_path}", "warning")
            self._data = {}
            self._ensure_default()
            self._ensure_schema()
            self.save()
            return

        # 确保有 meta section
        if "meta" not in self._data:
            self._data["meta"] = {}

        # 恢复活跃 section
        saved_active = self._data["meta"].get("active", "")
        if saved_active and saved_active in self._data:
            self._active_section = saved_active
        else:
            self._active_section = self.default_section
            self._data["meta"]["active"] = self.default_section

        # 自动补全缺失 key
        self._ensure_schema()
        self._dirty = False
        self._log(f"已加载 {len(self.sections)} 个配置, 活跃: {self._active_section}")

    def save(self):
        """写入 TOML 文件"""
        self._data["meta"] = self._data.get("meta", {})
        self._data["meta"]["active"] = self._active_section
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(_serialize_toml(self._data), encoding="utf-8")
        self._dirty = False
        self._log(f"配置已保存: {self.filepath.name}")

    # ── 读写当前活跃配置 ──────────────────────────────────────

    def get(self, key: str, default=None):
        """获取活跃 section 中某个 key 的值"""
        section = self._data.get(self._active_section, {})
        return section.get(key, default)

    def set(self, key: str, value, section: str | None = None):
        """设置某个 section 的 key 值"""
        sec = section or self._active_section
        if sec not in self._data:
            self._data[sec] = {}
        self._data[sec][key] = value
        self._dirty = True

    # ── 多 section 管理 ───────────────────────────────────────

    def get_section(self, name: str) -> dict:
        return dict(self._data.get(name, {}))

    def activate(self, name: str) -> bool:
        """切换活跃 section"""
        if name not in self._data:
            self._log(f"section 不存在: {name}", "error")
            return False
        self._active_section = name
        self._dirty = True
        self._log(f"切换到配置: {name}")
        return True

    def add_section(self, name: str, copy_from: str | None = None) -> bool:
        """新增 section，可复制已有 section 的值"""
        if name in self._data:
            return False
        if copy_from and copy_from in self._data:
            base = self._data[copy_from]
        else:
            base = {k: v["default"] for k, v in self.schema.items()}
        self._data[name] = dict(base)
        self._dirty = True
        self._log(f"新增配置: {name}")
        return True

    def delete_section(self, name: str) -> bool:
        """删除 section（不允许删除 default）"""
        if name == self.default_section or name not in self._data:
            return False
        del self._data[name]
        if self._active_section == name:
            self._active_section = self.default_section
        self._dirty = True
        self._log(f"删除配置: {name}")
        return True

    def as_dict(self) -> dict:
        """当前活跃 section 的完整 dict（含 section 名）"""
        result = dict(self._data.get(self._active_section, {}))
        result["_name"] = self._active_section
        return result

    def is_dirty(self) -> bool:
        return self._dirty

    # ── 内部 ──────────────────────────────────────────────────

    def _ensure_default(self):
        """确保 default section 存在"""
        if self.default_section not in self._data:
            self._data[self.default_section] = {}

    def _ensure_schema(self):
        """对所有已有 section 补充 schema 中定义的 key"""
        added = 0
        for sec_name in list(self._data.keys()):
            if sec_name == "meta":
                continue
            sec = self._data[sec_name]
            if not isinstance(sec, dict):
                sec = {}
                self._data[sec_name] = sec
            for key, meta in self.schema.items():
                if key not in sec:
                    sec[key] = deepcopy(meta["default"])
                    added += 1
        if added > 0:
            self._log(f"自动补充了 {added} 个新 key")
            self._dirty = True

    def _log(self, msg: str, level="info"):
        if self._logger:
            getattr(self._logger, level, self._logger.info)(f"[配置] {msg}")
