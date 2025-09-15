# apps/amount/config_loader.py
import configparser
import re
import os
from functools import lru_cache
from configparser import ConfigParser
from typing import Dict, List, Tuple, Union, TYPE_CHECKING
from apps.client.models import ClientType
from apps.documents.amount.constants import MIN_ENTRIES

if TYPE_CHECKING:
    from apps.documents.amount.models import AmountDocumentType  # 循環回避

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.ini")


# ===== 基本ユーティリティ =====
@lru_cache(maxsize=1) # 同じ引数で呼ばれた関数の結果をキャッシュする
def _get_config_parser() -> configparser.ConfigParser:
    """config.ini を読み込んだ ConfigParser を（プロセス内で）一度だけ返す。"""
    parser = configparser.ConfigParser()
    parser.read(CONFIG_FILE, encoding="utf-8")
    return parser


def _safe_int(value: Union[str, int, None]) -> int:
    """安全に int へ変換。失敗時は 0。"""
    try:
        return int(value)  # int はそのまま返る
    except (ValueError, TypeError):
        return 0


def natural_key(key: str) -> Tuple[str, int]:
    """
    'entry10' などを ('entry', 10) に分解する自然順キー。
    タプル比較で prefix → 数値 の順にソートされる。
    """
    m = re.match(r"([a-zA-Z]+)(\d+)", key or "")
    if m:
        prefix, num = m.groups()
        return prefix, int(num)
    return key, 0


# ===== 公開 API =====
def load_config() -> Dict[str, Union[Dict[str, str], Dict[str, float]]]:
    """主要な設定値を辞書形式で返す。"""
    parser = _get_config_parser()
    return {
        "OFFICE": dict(parser["OFFICE"]) if parser.has_section("OFFICE") else {},
        "BANK": dict(parser["BANK"]) if parser.has_section("BANK") else {},
        "TAX_RATE": {
            "consumption_tax": float(parser.get("TAX_RATE", "consumption_tax", fallback="0")),
            "withholding_exemption": int(parser.get("TAX_RATE", "withholding_exemption", fallback="0")),
            "withholding_tax": float(parser.get("TAX_RATE", "withholding_tax", fallback="0")),
        },
    }


def get_default_entries_for_client_type(client_type: ClientType) -> Dict[str, List[Union[str, int]]]:
    """
    クライアント種別（権利者・義務者・申請人）に応じた
    [item_types, reward_amounts, expense_amounts] のデフォルト行を返す。
    MIN_ENTRIES に満たない分は "" / 0 で埋める。
    """
    section_map = {
        ClientType.RIGHT_HOLDER: "DEFAULT_ENTRIES_RIGHT_HOLDER",
        ClientType.OBLIGATION_HOLDER: "DEFAULT_ENTRIES_OBLIGATION_HOLDER",
        ClientType.APPLICANT: "DEFAULT_ENTRIES_APPLICANT",
    }
    section_name = section_map.get(client_type)

    parser: ConfigParser = _get_config_parser()
    entries: Dict[str, List[Union[str, int]]]

    if section_name and parser.has_section(section_name):
        # キー(entry1, entry2, …)を自然順に並べ替えて値を取り出す
        values = [parser[section_name][k] for k in sorted(parser[section_name], key=natural_key)]
        entries = _build_default_entries(values)
    else:
        entries = {"item_types": [], "reward_amounts": [], "expense_amounts": []}

    # パディング
    for key in ("item_types", "reward_amounts", "expense_amounts"):
        while len(entries[key]) < MIN_ENTRIES:
            entries[key].append("" if key == "item_types" else 0)
    return entries


def get_note_default_for_client_type(client_type: ClientType) -> str:
    """
    クライアント種別ごとの NOTE_DEFAULTS を返す。
    - ClientType.RIGHT_HOLDER → ESTIMATE
    - ClientType.OBLIGATION_HOLDER → INVOICE
    - ClientType.APPLICANT → RECEIPT
    """
    section_map = {
        ClientType.RIGHT_HOLDER: "ESTIMATE",
        ClientType.OBLIGATION_HOLDER: "INVOICE",
        ClientType.APPLICANT: "RECEIPT",
    }

    parser = _get_config_parser()
    if not parser.has_section("NOTE_DEFAULTS"):
        return ""

    key = section_map.get(client_type)
    if not key:
        return ""

    # \n を実際の改行に変換
    return parser["NOTE_DEFAULTS"].get(key, "").replace("\\n", "\n")

def get_note_default_by_document_type(doc_type: "AmountDocumentType") -> str:
    """
    AmountDocumentType（例: ESTIMATE / INVOICE / RECEIPT）に対応する備考の初期値を返す。
    未定義なら空文字。
    """
    parser = _get_config_parser()
    if not parser.has_section("NOTE_DEFAULTS"):
        return ""
    # Enum.name をそのまま使い、\n を実改行に
    raw = parser["NOTE_DEFAULTS"].get(getattr(doc_type, "name", ""), "")
    return raw.replace("\\n", "\n")


# ===== 内部処理 =====
def _build_default_entries(values: List[str]) -> Dict[str, List[Union[str, int]]]:
    """
    '名称,報酬,実費' の CSV 形式の文字列リストから 3 配列を生成。
    不足フィールドは "" / 0 とする。
    """
    item_types: List[str] = []
    reward_amounts: List[int] = []
    expense_amounts: List[int] = []

    for raw in values:
        parts = [p.strip() for p in (raw or "").split(",")]
        item_types.append(parts[0] if len(parts) > 0 else "")
        reward_amounts.append(_safe_int(parts[1]) if len(parts) > 1 else 0)
        expense_amounts.append(_safe_int(parts[2]) if len(parts) > 2 else 0)

    return {
        "item_types": item_types,
        "reward_amounts": reward_amounts,
        "expense_amounts": expense_amounts,
    }