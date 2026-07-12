"""
Common FT test item name patterns for column header detection.
"""
import re

# Known test item root names (case-insensitive)
TEST_ITEM_ROOTS = [
    "IGSS", "IDSS", "VTH", "VF", "RDSON", "RDON", "RON",
    "ICES", "IGES", "VCESAT", "VCE", "VSAT", "VDS", "VGS",
    "BVDSS", "BVGSS", "BVDG", "VGD", "VBR",
    "CISS", "COSS", "CRSS", "QGD", "QGS", "QG",
    "VSD", "VFWD", "VREV", "IR", "IF",
    "GM", "GFS", "YFS",
    "TON", "TOFF", "TR", "TF", "TDON", "TDOFF",
    "ISC", "ILIM", "OCP", "SCP",
    "TEMP", "TSENSE",
    "VDD", "VCC", "VEE", "VSS",
    "IOUT", "IIN", "IQ", "ISUPPLY",
    "POWER", "EFF", "EFFICIENCY",
    "GAIN", "AV", "AVOL", "BW", "GBW",
    "PSRR", "CMRR", "SVR",
    "VOS", "IOFFSET", "IB",
    "TEST", "MEAS", "MEASUREMENT",
]

# Compiled regex: matches "IGSS_T1", "IDSS_2", "VTH_1", "DC_IGSS_1", etc.
TEST_ITEM_RE = re.compile(
    r'(?:^|_)(?:' + '|'.join(TEST_ITEM_ROOTS) + r')(?:_\d+|_\w+)?$',
    re.IGNORECASE
)


def is_test_item_column(col_name: str) -> bool:
    """Check if a column name looks like a test parameter column."""
    return bool(TEST_ITEM_RE.search(col_name.strip()))


def count_test_item_columns(columns: list[str]) -> int:
    """Count how many columns in a list look like test items."""
    return sum(1 for c in columns if is_test_item_column(c))


def find_test_item_header_row(rows: list[list[str]]) -> int:
    """Find the row index that has the most test-item-like columns.
    
    Scans all rows and returns the index of the row with the highest
    test-item column count. This identifies the actual data column header.
    """
    best_idx = 0
    best_count = 0
    for i, row in enumerate(rows):
        count = count_test_item_columns(row)
        if count > best_count:
            best_count = count
            best_idx = i
    return best_idx
