# apps/commerce/shared/jp_amount.py

import re
from typing import Optional

from apps.register.commerce.pdf.services.normalize import ZEN2HAN

def jp_amount_to_int(s: str) -> Optional[int]:
    """
    日本語の額面・株数を整数へ正規化。
    - 金額: 億／万／円 を合成。例）金１億２５００万円 → 125_000_000
    - 株数: 万株 → *10,000。例）１万株 → 10_000
    - 失敗時 None
    """
    s2 = s.translate(ZEN2HAN).replace(",", "")
    # --- 金額（円） ---
    if "金" in s2 and ("円" in s2 or "万円" in s2 or "億円" in s2):
        total = 0
        matched = False
        m_oku = re.search(r"(\d+)\s*億", s2)
        if m_oku:
            total += int(m_oku.group(1)) * 100_000_000
            matched = True
        m_man = re.search(r"(\d+)\s*万", s2)
        if m_man:
            total += int(m_man.group(1)) * 10_000
            matched = True
        # 「金800万円」「金800円」などの簡易
        m_simple_man = re.search(r"金\s*(\d+)\s*万円", s2)
        if m_simple_man:
            return int(m_simple_man.group(1)) * 10_000
        m_simple_yen = re.search(r"金\s*(\d+)\s*円", s2)
        if m_simple_yen:
            return int(m_simple_yen.group(1))
        return total if matched else None

    # --- 株数 ---
    base = 0
    m_man = re.search(r"(\d+)\s*万", s2)   # 「１万株」の「万」
    if m_man:
        base += int(m_man.group(1)) * 10_000
    m_num = re.search(r"(\d+)\s*株", s2)   # 数字＋株
    if m_num:
        return base or int(m_num.group(1))
    return None