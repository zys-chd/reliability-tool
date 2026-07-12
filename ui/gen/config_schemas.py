#!/usr/bin/env python3
"""
Config schema for FTDataAnalisys.
一个配置文件，多 section，每个 section 包含所有 tab 的配置项。
"""

from pathlib import Path

FT_ANALYSIS_SCHEMA = {
    # ── 分组配置 ──
    "group_mode": {
        "default": "by_name",
        "type": str,
        "label": "分组方式",
        "tab": "group",
        "options": ["by_name", "by_sn", "both"],
    },
    "sn_pattern": {
        "default": "",
        "type": str,
        "label": "SN 匹配模式",
        "tab": "group",
    },
    "file_pattern": {
        "default": "",
        "type": str,
        "label": "文件名匹配模式",
        "tab": "group",
    },

    # ── 模板配置 ──
    "template_dir": {
        "default": "",
        "type": str,
        "label": "模板文件目录",
        "tab": "template",
    },
    "test_items_path": {
        "default": "",
        "type": str,
        "label": "测试项配置文件路径",
        "tab": "template",
    },
    "calc_limit_path": {
        "default": "",
        "type": str,
        "label": "计算/Limit 配置路径",
        "tab": "template",
    },
    "ut_config_path": {
        "default": "",
        "type": str,
        "label": "UT 配置路径",
        "tab": "template",
    },

    # ── 文件路径配置 ──
    "tx_merge_path": {
        "default": str(Path("%DIR_TO_TX_FILE%") / "TX合并.xlsx"),
        "type": str,
        "label": "合并结果路径",
        "tab": "paths",
    },
    "compare_path": {
        "default": str(Path("%DIR_TO_TX_FILE%") / "对比.xlsx"),
        "type": str,
        "label": "对比结果路径",
        "tab": "paths",
    },
    "t0_file_list": {
        "default": [],
        "type": list,
        "label": "T0 文件列表",
        "tab": "files",
    },
    "tx_file_list": {
        "default": [],
        "type": list,
        "label": "TX 文件列表",
        "tab": "files",
    },

    # ── 绘图配置 ──
    "x_axis": {
        "default": "",
        "type": str,
        "label": "X 轴字段",
        "tab": "plot",
    },
    "y_axis": {
        "default": "",
        "type": str,
        "label": "Y 轴字段",
        "tab": "plot",
    },
    "plot_type": {
        "default": "line",
        "type": str,
        "label": "图表类型",
        "tab": "plot",
        "options": ["line", "scatter", "bar", "box", "hist"],
    },
    "title": {
        "default": "",
        "type": str,
        "label": "图表标题",
        "tab": "plot",
    },
    "save_dir": {
        "default": "",
        "type": str,
        "label": "图片保存目录",
        "tab": "plot",
    },
}

TDDB_SCHEMA = {
    "file_path": {
        "default": "",
        "type": str,
        "label": "TDDB 数据文件路径",
    },
    "sheet_name": {
        "default": "",
        "type": str,
        "label": "Excel sheet 名称",
    },
    "work_voltage": {
        "default": "3.3",
        "type": str,
        "label": "工作电压/V",
    },
    "oxide_thickness": {
        "default": "5.0",
        "type": str,
        "label": "栅氧厚度/nm",
    },
    "work_temperature": {
        "default": "25",
        "type": str,
        "label": "工作温度/℃",
    },
    "tddb_model": {
        "default": "E模型",
        "type": str,
        "label": "TDDB 模型",
    },
    "pick_method": {
        "default": "weibull曲线取点",
        "type": str,
        "label": "取点方式",
    },
    "save_dir": {
        "default": "",
        "type": str,
        "label": "临时保存目录",
    },
}

GLOBAL_SCHEMA = {
    "window_width": {
        "default": 910,
        "type": int,
        "label": "窗口宽度",
    },
    "window_height": {
        "default": 692,
        "type": int,
        "label": "窗口高度",
    },
    "window_position": {
        "default": "记忆上次关闭时位置",
        "type": str,
        "label": "窗口启动位置",
        "options": ["记忆上次关闭时位置", "中心", "左上", "右上", "左下", "右下", "上方", "下方", "左方", "右方"],
    },
    "window_geometry": {
        "default": "",
        "type": str,
        "label": "窗口几何信息（自动保存）",
    },
    "font_size": {
        "default": 12,
        "type": int,
        "label": "默认字体大小",
    },
    "font_cn": {
        "default": "",
        "type": str,
        "label": "默认中文字体",
    },
    "font_en": {
        "default": "",
        "type": str,
        "label": "默认西文字体",
    },
    "clean_on_exit": {
        "default": "是",
        "type": str,
        "label": "退出前清理文件",
        "options": ["是", "否"],
    },
}
