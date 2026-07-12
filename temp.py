import pandas as pd


def creat_TDDB_template():
    data = {
        "PART_ID": [],
        "Vgs": [],
        "TBD": [],
        "TBD unit": [],
        "QBD": [],
        "QBD unit": [],
        "ignore": [],
        "group": [],
        "channel": [],
        "comment": [],
    }

    pd.DataFrame(data).to_excel("./TDDB_template.xlsx")


def creat_FT_template():
    data = {
        "PART_ID": ["lower limit", "higher limit", "formula", "limit", "limit_side"],
        "SOFT_BIN": ["", "", "", "", ""],
        "group": ["", "", "", "", ""],
        "file": ["", "", "", "", ""],
        "^(?=.IGSS)(?!.Delta)(?!.Post).*": ["", "", "", "", ""],
    }
    pd.DataFrame(data).to_excel("./FT_template.xlsx")

creat_TDDB_template()
creat_FT_template()
# python
import re

pattern = r'^(?!.*Delta)(?!.*Post).*IGSS.*$'
# pattern = r'^(?=.IGSS)(?!.Delta)(?!.Post).*$'
texts = [
    "这是IGSS测试文本",
    "包含IGSS和Post的文本",
    "Delta和IGSS都在",
    "只有IGSS没有其他",
    "IGSS"
]

for text in texts:
    res = re.findall(pattern, text)
    if res:
        print(f"✓ 匹配: {text} {res}")
    else:
        print(f"✗ 不匹配: {text} {res}")