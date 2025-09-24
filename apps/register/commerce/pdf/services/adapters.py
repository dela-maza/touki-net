# apps/register/commerce/pdf/services/adapters.py
from typing import List, Tuple
from .structures import Line, EntryBlock, RegistryItem, RegistrySection

# sections_with_items: List[Tuple[str, List[List[List[str]]]]]
#    = [(sec_text, items)]  where items = [ [subitem(lines...) ...], ... ]
def to_registry_sections(
        sections_with_items: List[Tuple[str, List[List[List[str]]]]]
) -> List[RegistrySection]:
    sections: List[RegistrySection] = []

    for sec_text, items in sections_with_items:
        reg_items: List[RegistryItem] = []
        title_guess = "セクション"

        for item_subitems in items:
            # item_subitems: List[List[str]]  ← サブアイテム（変更ブロック）ごとの生行
            blocks: List[EntryBlock] = []
            for sub_lines in item_subitems:
                # サブアイテムの各行を Line に
                lines = [Line(t) for t in sub_lines]
                blocks.append(EntryBlock(lines=lines))
            reg_items.append(RegistryItem(entry_blocks=blocks))

        # タイトル当て（最初のアイテムの最初のブロックの最初の行の label を借りる）
        if reg_items and reg_items[0].entry_blocks and reg_items[0].entry_blocks[0].lines:
            label, _, _ = reg_items[0].entry_blocks[0].lines[0].parse_cells()
            if label:
                title_guess = label

        sections.append(RegistrySection(raw_text=sec_text, title=title_guess, registry_item=reg_items))

    return sections