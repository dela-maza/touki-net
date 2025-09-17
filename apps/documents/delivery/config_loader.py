# apps/documents/delivery/config_loader.py
import os, configparser, re
from functools import lru_cache
from typing import Dict, List, Tuple
from apps.client.models import ClientType  # ★ これを使って分岐

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.ini")
MIN_ROWS = 10  # 足りない分は空行で埋める

@lru_cache(maxsize=1)
def _p() -> configparser.ConfigParser:
    c = configparser.ConfigParser()
    c.read(CONFIG_FILE, encoding="utf-8")
    return c

def load_paragraphs() -> dict[str, str]:
    s = _p()["PARAGRAPH"] if _p().has_section("PARAGRAPH") else {}
    g = (s.get("GREETING", "")).replace("\\n", "\n")
    c = (s.get("CLOSING",  "")).replace("\\n", "\n")
    return {"greeting": g, "closing": c}

# ---- 既定行の読み込み ----
def _natural_key(k: str) -> Tuple[str, int]:
    m = re.match(r"([a-zA-Z]+)(\d+)", k or "")
    if m:
        return m.group(1), int(m.group(2))
    return k, 0

def _parse_entry_line(raw: str) -> Dict[str, str]:
    """
    形式: '書類名,枚数'（枚数が空でもOK）
    """
    if raw is None:
        return {"doc_name": "", "copies": ""}

    parts = [p.strip() for p in str(raw).split(",")]
    nonempty = [p for p in parts if p != ""]

    if not nonempty:
        return {"doc_name": "", "copies": ""}

    # 1要素: 書類名のみ
    if len(nonempty) == 1:
        return {"doc_name": nonempty[0], "copies": ""}

    # 2要素以上: 先頭=書類名, 最後=枚数 とみなす
    return {"doc_name": nonempty[0], "copies": nonempty[-1]}

def _load_entries(section_name: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if _p().has_section(section_name):
        sec = _p()[section_name]
        for key in sorted(sec.keys(), key=_natural_key):
            rows.append(_parse_entry_line(sec.get(key, "")))

    # 行数を MIN_ROWS に揃える
    while len(rows) < MIN_ROWS:
        rows.append({"doc_name": "", "copies": ""})
    return rows

_SECTION_MAP = {
    ClientType.RIGHT_HOLDER:      "DEFAULT_DOCUMENT_RIGHT_HOLDER",
    ClientType.OBLIGATION_HOLDER: "DEFAULT_DOCUMENT_OBLIGATION_HOLDER",
    # 申請人など他の種別が来たときのフォールバック
    ClientType.APPLICANT:         "DEFAULT_DOCUMENT_RIGHT_HOLDER",
}

def get_default_documents(client_type: ClientType) -> List[Dict[str, str]]:
    sec = _SECTION_MAP.get(client_type)
    if not sec:
        return [{"doc_name": "", "copies": ""} for _ in range(MIN_ROWS)]
    return _load_entries(sec)

# 既存のダミー行APIも残しておく（既存呼び出しがあっても壊れないように）
def default_rows(n: int = 10) -> list[dict[str, str]]:
    return [{"doc_name": "", "copies": ""} for _ in range(n)]