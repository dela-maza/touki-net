# apps/documents/origin/config_loader.py
from __future__ import annotations
import os, configparser
from functools import lru_cache
from typing import List, Dict, Optional
from datetime import date
from apps.shared.wareki import iso_str_to_wareki

from .constants import CauseType

# このファイル（config.ini）は apps/documents/origin/ 配下に置く前提
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.ini")


# ----------------------------
# 基本：config.ini ローダ
# ----------------------------
@lru_cache(maxsize=1)
def _parser() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.optionxform = str  # 大文字・小文字保持
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"origin config.ini not found: {CONFIG_FILE}")
    cp.read(CONFIG_FILE, encoding="utf-8")
    return cp


# ----------------------------
# 1) テンプレ（行ごと）を取得
# ----------------------------
def get_cause_templates(cause_type: CauseType) -> List[str]:
    """
    指定 cause_type のセクション（例: 'SALE'）から CAUSE_FACT_1, 2... を順に返す。
    """
    cp = _parser()
    sec = cause_type.name  # SALE / GIFT / DIVISION
    if not cp.has_section(sec):
        return []

    items = []
    for k, v in cp.items(sec):
        if k.startswith("CAUSE_FACT_"):
            try:
                idx = int(k.replace("CAUSE_FACT_", "").strip())
            except ValueError:
                continue
            items.append((idx, v))

    items.sort(key=lambda x: x[0])
    return [v for _, v in items]


# ----------------------------
# 2) プレースホルダを埋めて返す
# ----------------------------
def _fmt_date(d: Optional[date]) -> str:
    return "" if not d else iso_str_to_wareki(d)


def render_cause_lines(
        cause_type: CauseType,
        *,
        contract_date: Optional[date] = None,
        execution_date: Optional[date] = None,
        extra_ctx: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    config.ini の行テンプレートに {{ contract_date }} / {{ execution_date }} を埋める。
    """
    tmpl_lines = get_cause_templates(cause_type)
    if not tmpl_lines:
        return []

    ctx = {
        "contract_date": _fmt_date(contract_date),
        "execution_date": _fmt_date(execution_date),
    }
    if extra_ctx:
        ctx.update({k: ("" if v is None else str(v)) for k, v in extra_ctx.items()})

    def _render_one(s: str) -> str:
        out = s
        for k, v in ctx.items():
            out = out.replace(f"{{{{ {k} }}}}", v)
        return out

    return [_render_one(s) for s in tmpl_lines]


# ----------------------------
# 3) まとめて文字列化
# ----------------------------
def render_cause_fact(
        cause_type: CauseType,
        *,
        contract_date: Optional[date] = None,
        execution_date: Optional[date] = None,
        joiner: str = "\n",
        extra_ctx: Optional[Dict[str, str]] = None,
) -> str:
    """
    行を join して一つのテキストにする。
    """
    lines = render_cause_lines(
        cause_type,
        contract_date=contract_date,
        execution_date=execution_date,
        extra_ctx=extra_ctx,
    )
    return joiner.join(lines)