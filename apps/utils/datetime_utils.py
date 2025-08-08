### apps/utils/datetime_utils.py
from datetime import date


def to_japanese_era(d: date) -> str:
    """日付を和暦表記に変換する（例: 令和7年7月7日）"""
    if d >= date(2019, 5, 1):
        return f"令和{d.year - 2018}年{d.month}月{d.day}日"
    elif d >= date(1989, 1, 8):
        return f"平成{d.year - 1988}年{d.month}月{d.day}日"
    elif d >= date(1926, 12, 25):
        return f"昭和{d.year - 1925}年{d.month}月{d.day}日"
    elif d >= date(1912, 7, 30):
        return f"大正{d.year - 1911}年{d.month}月{d.day}日"
    else:
        return f"明治{d.year - 1867}年{d.month}月{d.day}日"
