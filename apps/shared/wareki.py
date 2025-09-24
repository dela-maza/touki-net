# apps/shared/wareki.py
import re
from datetime import date

# === 和暦文字列 → ISO文字列 ===
def wareki_str_to_iso(s: str) -> str | None:
    """和暦文字列 (例: 令和5年10月16日) を ISO (YYYY-MM-DD) に変換。抽出失敗時 None。"""
    ZEN2HAN = str.maketrans("０１２３４５６７８９－，/", "0123456789-,/")
    s2 = (s or "").translate(ZEN2HAN)
    m = re.search(r"(令和|平成|昭和|大正|明治)\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日", s2)
    if not m:
        return None
    era, y, mo, d = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    base = {"令和": 2018, "平成": 1988, "昭和": 1925, "大正": 1911, "明治": 1867}.get(era)
    if base is None:
        return None
    year = base + y
    return f"{year:04d}-{mo:02d}-{d:02d}"

# === ISO文字列 → 和暦文字列 ===
def iso_str_to_wareki(iso_date: str) -> str:
    """ISO (YYYY-MM-DD) を和暦文字列に変換。失敗時は元文字列を返す。"""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", iso_date or "")
    if not m:
        return iso_date
    y, mo, d = map(int, m.groups())
    return date_to_wareki(date(y, mo, d))

# === Python date → 和暦文字列 ===
def date_to_wareki(d: date) -> str:
    """datetime.date を和暦文字列に変換。"""
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