# apps/register/parser/commerce/normalise.py

import re
from datetime import date

ZEN = "０１２３４５６７８９，．－："
HAN = "0123456789,.-:"
TRANS = str.maketrans(ZEN, HAN)

def normalize_text(s: str) -> str:
    s = s.translate(TRANS)
    s = re.sub(r"[ \t]+", " ", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s.strip()

def wareki_to_seireki(s: str) -> str | None:
    # 令和/平成/昭和 → YYYY-MM-DD の簡易変換（実装は後で厳密化）
    return None