# apps/register/commerce/pdf/services/debug_utils.py
from __future__ import annotations
import re
from typing import List, Tuple

from .normalize import BOX_CHARS

# 公開する型エイリアス
SubItem = List[str]               # 変更情報1つの行群
Item = List[SubItem]              # 項目 = サブアイテム(SubItem)のリスト
Section = Tuple[str, List[Item]]  # (セクション全文, 項目(Item)のリスト)




__all__ = [
    "SubItem",
    "Item",
    "Section",
    "is_box_only",
    "split_subitems",
    "split_block_items",
    "split_section_blocks",
]

def is_box_only(line: str) -> bool:
    """行が罫線だけで構成されているか判定"""
    s = line.strip()
    return bool(s) and all(ch in (BOX_CHARS + "┼┬┴├┤") for ch in s)

def split_subitems(item_lines: List[str]) -> List[List[str]]:
    """
    1項目ブロックを '┃ ├' 区切りでさらに分割。
    - 罫線だけの行は削除
    - 区切り行自体もスキップ
    """
    subitems: List[List[str]] = []
    buffer: List[str] = []

    for ln in item_lines:
        if is_box_only(ln):
            continue
        if "┃ ├" in ln:  # サブアイテム区切り
            if buffer:
                subitems.append(buffer)
                buffer = []
            continue
        buffer.append(ln)

    if buffer:
        subitems.append(buffer)

    return subitems

def split_block_items(section_block: str) -> List[List[List[str]]]:
    """
    セクション文字列を '┠' 区切りで項目ごとに分割。
    各項目はさらに split_subitems() で分割（3階層）。
    """
    items: List[List[List[str]]] = []
    for block in section_block.split("┠"):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if lines:
            items.append(split_subitems(lines))
    return items

def split_section_blocks(norm: str) -> List[Section]:
    """
    正規化済みテキストを '┣' で分割。
    返り値: [(セクション全文, セクション内 items(→subitems)), ...]
    """
    result: List[Section] = []
    sections = [s for s in norm.split("┣") if s.strip()]

    for sec in sections:
        lines = sec.splitlines()

        # 先頭が罫線だけ（装飾）の場合は落とす
        if lines and re.fullmatch(r"[━┯┷┿┓┫┛]+", lines[0]):
            lines = lines[1:]

        sec_clean = "\n".join(lines).strip()
        if not sec_clean:
            continue

        items = split_block_items(sec_clean)
        result.append((sec_clean, items))

    return result