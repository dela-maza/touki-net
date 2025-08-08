### amount_document/config_loader.py
import configparser
import re
import os
from typing import Union
from apps.client.models import ClientType
from apps.amount_document.constants import MIN_ENTRIES
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.amount_document.models import AmountDocumentType  # 循環インポートの回避

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.ini")


def get_config_parser() -> configparser.ConfigParser:
    """ConfigParserの初期化と読み込み"""
    parser = configparser.ConfigParser()
    parser.read(CONFIG_FILE, encoding="utf-8")
    return parser


def load_config() -> dict:
    """主要な設定値を辞書形式で返す"""
    parser = get_config_parser()
    return {
        "OFFICE": dict(parser["OFFICE"]),
        "BANK": dict(parser["BANK"]),
        "TAX_RATE": {
            "consumption_tax": float(parser["TAX_RATE"]["consumption_tax"]),
            "withholding_exemption": int(parser["TAX_RATE"]["withholding_exemption"]),
            "withholding_tax": float(parser["TAX_RATE"]["withholding_tax"]),
        }
    }


def _safe_int(value: str) -> int:
    """安全にintへ変換。失敗時は0を返す"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _build_default_entries(values: list[str]) -> dict[str, Union[str, int, list]]:
    """項目のリストから item_type, reward, expense のリストを生成"""
    item_types, reward_amounts, expense_amounts = [], [], []

    for raw in values:
        parts = [p.strip() for p in raw.split(",")]
        item_types.append(parts[0] if len(parts) > 0 else "")
        reward_amounts.append(_safe_int(parts[1]) if len(parts) > 1 else 0)
        expense_amounts.append(_safe_int(parts[2]) if len(parts) > 2 else 0)

    return {
        "item_types": item_types,
        "reward_amounts": reward_amounts,
        "expense_amounts": expense_amounts
    }


def natural_key(key: str):
    match = re.match(r'([a-zA-Z]+)(\d+)', key)
    if match:
        prefix, num = match.groups()
        return prefix, int(num)
    return key, 0


def get_default_entries_for_client_type(client_type: ClientType) -> dict:
    """クライアント種別に応じたデフォルトエントリを取得し、MIN_ENTRIES分埋める"""
    section_map = {
        ClientType.RIGHT_HOLDER: "DEFAULT_ENTRIES_RIGHT_HOLDER",
        ClientType.OBLIGATION_HOLDER: "DEFAULT_ENTRIES_OBLIGATION_HOLDER",
        ClientType.APPLICANT: "DEFAULT_ENTRIES_APPLICANT",
    }

    section_name = section_map.get(client_type)
    parser = get_config_parser()

    if section_name and parser.has_section(section_name):
        # ["entry1", "entry10", "entry2", ...]を
        # ["entry1", "entry2", ... "entry10", ...]のように自然順（数字の大小を考慮）で並べ替える
        # sortedはプレフィックス "entry" を文字列比較し、同じなら数字部分 1, 2, 10 ... を整数として昇順にソートする
        values = [parser[section_name][key] for key in sorted(parser[section_name], key=natural_key)]
        entries = _build_default_entries(values)
    else:
        entries = {
            "item_types": [],
            "reward_amounts": [],
            "expense_amounts": []
        }

    # MIN_ENTRIES分になるように空白・0で埋める
    for key in ("item_types", "reward_amounts", "expense_amounts"):
        while len(entries[key]) < MIN_ENTRIES:
            entries[key].append("" if key == "item_types" else 0)

    return entries


def get_note_default_by_document_type(doc_type: 'AmountDocumentType') -> str:
    """AmountDocumentType に応じた備考の初期値を取得"""
    parser = get_config_parser()
    try:
        return parser["NOTE_DEFAULTS"][doc_type.name]
    except KeyError:
        return ""
