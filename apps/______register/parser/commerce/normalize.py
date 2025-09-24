# apps/commerce/services/commerce/normalize.py
import re

_Z2H = str.maketrans(
    "０１２３４５６７８９：，．－―ー／　",
    "0123456789:,.---/ "
)

# よく出る罫線類は全部 '|' に寄せる
_BOX = re.compile(r"[┃│｜┆┇┋┊╎╏┤├┼┬┴┐┌┘└―─━]+")
_WS  = re.compile(r"\s+")

def normalize_line(s: str) -> str:
    if not s:
        return ""

    s = s.translate(_Z2H)         # 全角→半角
    s = _BOX.sub("|", s)          # 罫線→ '|'
    s = _WS.sub(" ", s).strip()   # 余分な空白を詰める
    return s