# apps/required_document/config_loader.py

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
    if raw is None:
        return {"name": "", "note": "", "copies": ""}

    parts = [p.strip() for p in str(raw).split(",")]
    nonempty = [p for p in parts if p != ""]

    if not nonempty:
        return {"name": "", "note": "", "copies": ""}

    if len(nonempty) == 1:
        name, note, copies = nonempty[0], "", ""
    elif len(nonempty) == 2:
        name, note, copies = nonempty[0], "", nonempty[1]
    else:
        name, note, copies = nonempty[0], nonempty[1], nonempty[-1]

    return {"name": name, "note": note, "copies": copies}


def load_paragraphs() -> Dict[str, str]:
    p = _get_parser()
    s = p["PARAGRAPH"] if p.has_section("PARAGRAPH") else {}
    greeting = s.get("GREETING_PARAGRAPH", "").replace("\\n", "\n")
    main = s.get("MAIN_PARAGRAPH", "").replace("\\n", "\n")
    closing = (s.get("CLOSING_PARAGRAPH") or s.get("CROSSING_PARAGRAPH", "")).replace("\\n", "\n")
    return {"greeting": greeting, "main": main, "closing": closing}


def _load_entries(section_name: str) -> List[Dict[str, str]]:
    p = _get_parser()
    rows: List[Dict[str, str]] = []
    if p.has_section(section_name):
        sec = p[section_name]
        for key in sorted(sec.keys(), key=_natural_key):
            rows.append(_parse_entry_line(sec[key]))
    # MIN_ROWS に揃える
    while len(rows) < MIN_ROWS:
        rows.append({"name": "", "note": "", "copies": ""})
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
    sec = _SECTION_MAP.get(client_type)
    if not sec:
        empty_rows = [{"name": "", "note": "", "copies": ""} for _ in range(MIN_ROWS)]
        return {"mailed": empty_rows, "requested": empty_rows}

    mailed = _load_entries(sec["mailed"])
    requested = _load_entries(sec["requested"])
    return {"mailed": mailed, "requested": requested}