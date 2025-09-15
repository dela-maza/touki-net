# apps/documents/required/config_loader.py

import os
import re
import configparser
from functools import lru_cache
from typing import Dict, List, Tuple
from apps.client.models import ClientType

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.ini")
MIN_ROWS = 10   # すべてのデフォルトエントリをこの行数に揃える


@lru_cache(maxsize=1)
def _get_parser() -> configparser.ConfigParser:
    p = configparser.ConfigParser()
    p.read(CONFIG_FILE, encoding="utf-8")
    return p


def _natural_key(k: str) -> Tuple[str, int]:
    m = re.match(r"([a-zA-Z]+)(\d+)", k or "")
    if m:
        return m.group(1), int(m.group(2))
    return k, 0


def _parse_entry_line(raw: str) -> Dict[str, str]:
    """
    INIの1行（例: '委任状,署名1箇所,1通'）を doc_name/note/copies に分解。
    空やカンマ不足も許容して空文字で埋める。
    """
    if raw is None:
        return {"doc_name": "", "note": "", "copies": ""}

    parts = [p.strip() for p in str(raw).split(",")]
    nonempty = [p for p in parts if p != ""]

    if not nonempty:
        return {"doc_name": "", "note": "", "copies": ""}

    if len(nonempty) == 1:
        doc_name, note, copies = nonempty[0], "", ""
    elif len(nonempty) == 2:
        doc_name, note, copies = nonempty[0], "", nonempty[1]
    else:
        doc_name, note, copies = nonempty[0], nonempty[1], nonempty[-1]

    return {"doc_name": doc_name, "note": note, "copies": copies}


def load_paragraphs() -> Dict[str, str]:
    """
    [PARAGRAPH] を読み込み、\\n を実際の改行に変換して返す。
    keys: greeting / main / closing
    """
    p = _get_parser()
    s = p["PARAGRAPH"] if p.has_section("PARAGRAPH") else {}
    greeting = s.get("GREETING_PARAGRAPH", "").replace("\\n", "\n")
    main = s.get("MAIN_PARAGRAPH", "").replace("\\n", "\n")
    closing = (s.get("CLOSING_PARAGRAPH") or s.get("CROSSING_PARAGRAPH", "")).replace("\\n", "\n")
    return {"greeting": greeting, "main": main, "closing": closing}


def _load_entries(section_name: str) -> List[Dict[str, str]]:
    """
    指定セクションの entryX を自然順で読み、行数を MIN_ROWS にパディング。
    戻り値は [{doc_name, note, copies}, ...]
    """
    p = _get_parser()
    rows: List[Dict[str, str]] = []
    if p.has_section(section_name):
        sec = p[section_name]
        for key in sorted(sec.keys(), key=_natural_key):
            rows.append(_parse_entry_line(sec[key]))
    while len(rows) < MIN_ROWS:
        rows.append({"doc_name": "", "note": "", "copies": ""})
    return rows


_SECTION_MAP = {
    ClientType.RIGHT_HOLDER: {
        "mailed":    "DEFAULT_MAILED_DOCUMENT_RIGHT_HOLDER",
        "requested": "DEFAULT_REQUESTED_RETURN_DOCUMENT_RIGHT_HOLDER",
    },
    ClientType.OBLIGATION_HOLDER: {
        "mailed":    "DEFAULT_MAILED_DOCUMENT_OBLIGATION_HOLDER",
        "requested": "DEFAULT_REQUESTED_RETURN_DOCUMENT_OBLIGATION_HOLDER",
    },
}


def get_required_doc_defaults(client_type: ClientType) -> Dict[str, List[Dict[str, str]]]:
    """
    クライアント種別に応じ、送付/返送の既定行を返す。
    戻り値:
      {
        "mailed":    [{doc_name, note, copies}, ...],
        "requested": [{doc_name, note, copies}, ...]
      }
    """
    sec = _SECTION_MAP.get(client_type)
    if not sec:
        empty = [{"doc_name": "", "note": "", "copies": ""} for _ in range(MIN_ROWS)]
        return {"mailed": empty, "requested": empty}

    mailed = _load_entries(sec["mailed"])
    requested = _load_entries(sec["requested"])
    return {"mailed": mailed, "requested": requested}