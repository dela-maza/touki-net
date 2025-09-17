# apps/documents/origin/config_loader.py
from __future__ import annotations
import os, configparser
from functools import lru_cache
from typing import Iterable, List, Dict, Optional
from datetime import date, datetime

from .constants import CauseType

# このファイル（config.ini）は apps/documents/origin/ 配下に置く前提
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.ini")


# ----------------------------
# 基本：config.ini ローダ
# ----------------------------
@lru_cache(maxsize=1)
def _parser() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    # 大文字・小文字を区別したいので option 名の小文字化を抑止
    cp.optionxform = str
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"origin config.ini not found: {CONFIG_FILE}")
    cp.read(CONFIG_FILE, encoding="utf-8")
    return cp


# ----------------------------
# 1) テンプレ（行ごと）を取得
# ----------------------------
def get_cause_templates(cause_type: CauseType) -> List[str]:
    """
    指定 cause_type のセクション（例: 'SALE'）から line1, line2, ... を
    連番順にリストで返す。未定義なら空リスト。
    """
    cp = _parser()
    sec = cause_type.name  # SALE / GIFT / DIVISION
    if not cp.has_section(sec):
        return []

    # 'line' で始まるキーだけを拾い、数字でソート
    items = []
    for k, v in cp.items(sec):
        if k.startswith("line"):
            try:
                idx = int(k.replace("line", "").strip())
            except ValueError:
                continue
            items.append((idx, v))
    items.sort(key=lambda x: x[0])
    return [v for _, v in items]


# ----------------------------
# 2) プレースホルダを埋めて返す
# ----------------------------
def _fmt_date(d: Optional[date]) -> str:
    if not d:
        return ""
    # 必要なら和暦などに差し替え可
    return d.strftime("%Y-%m-%d")


def render_cause_lines(
        cause_type: CauseType,
        *,
        contract_date: Optional[date] = None,
        payment_date: Optional[date] = None,
        extra_ctx: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    config.ini の行テンプレートに {{ contract_date }} / {{ payment_date }} をはめて
    行ごとの文字列リストを返す。未定義の変数は空文字に置換。
    （シンプルな置換器：Jinja を使わず {{ var }} だけ対応）
    """
    tmpl_lines = get_cause_templates(cause_type)
    if not tmpl_lines:
        return []

    ctx = {
        "contract_date": _fmt_date(contract_date),
        "payment_date": _fmt_date(payment_date),
    }
    if extra_ctx:
        ctx.update({k: ("" if v is None else str(v)) for k, v in extra_ctx.items()})

    def _render_one(s: str) -> str:
        out = s
        for k, v in ctx.items():
            out = out.replace(f"{{{{ {k} }}}}", v)   # "{{ k }}" の置換
        return out

    return [_render_one(s) for s in tmpl_lines]


# ----------------------------
# 3) 1つのテキストにまとめたい時用
# ----------------------------
def render_cause_text(
        cause_type: CauseType,
        *,
        contract_date: Optional[date] = None,
        payment_date: Optional[date] = None,
        joiner: str = "\n",
        extra_ctx: Optional[Dict[str, str]] = None,
) -> str:
    """
    行リストを join して1つのテキストにして返す。
    詳細画面で <li> にしたい場合は render_cause_lines() を使ってください。
    """
    lines = render_cause_lines(
        cause_type,
        contract_date=contract_date,
        payment_date=payment_date,
        extra_ctx=extra_ctx,
    )
    return joiner.join(lines)