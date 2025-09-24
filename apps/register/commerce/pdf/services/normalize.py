# apps/register/commerce/pdf/services/normalize.py

import re

# =========================
# 2) 正規化（ノイズ除去・空白折り畳み）
# =========================

BOX_CHARS = "━─│┏┓┗┛┠┨┿┯┷┳┻"
ZEN2HAN = str.maketrans("０１２３４５６７８９－，", "0123456789-,")

def extract_table_block(text: str) -> str:
    """
    商業登記簿PDFのテキストから表部分だけを抽出する。
    - 先頭のヘッダ（「YYYY/MM/DD ... 現在の情報です」「住所」「会社名」など）をスキップ
    - 最初の「┏」または「┣」から開始
    - 最後の「┛」または「┗」で終了
    - それ以降の注意書きは落とす
    """
    lines = text.splitlines()

    start_idx = None
    end_idx = None

    for i, ln in enumerate(lines):
        if "┏" in ln or "┣" in ln:
            start_idx = i
            break

    for i in range(len(lines) - 1, -1, -1):
        if "┛" in lines[i] or "┗" in lines[i]:
            end_idx = i
            break

    # end_idx を含めて、それ以降の注意書きは落とす
    if start_idx is not None and end_idx is not None and start_idx <= end_idx:
        return "\n".join(lines[start_idx:end_idx+1])
    return text


def normalize_text(t: str) -> str:
    """
    正規化：
      - 全角空白→半角
      - 数字や符号の全角→半角
      - ┏ / ┗ を ┣ に統一
      - 罫線は同じ文字の連続だけ圧縮（例: ━━━ → ━）
      - 連続空白の圧縮
      - 行頭/行末の空白トリム
    """
    t = extract_table_block(t)
    t = t.replace("\u3000", " ")      # 全角空白→半角
    t = t.translate(ZEN2HAN)          # 数字など半角化

    # ┏ / ┗ を ┣ に統一（セクション区切りを一本化）
    t = t.replace("┏", "┣").replace("┗", "┣")

    # 罫線の連続を1文字にまとめる
    for ch in BOX_CHARS:
        t = re.sub(f"{ch}+", ch, t)

    # 空白を整理
    t = re.sub(r"[ \t]+", " ", t)
    t = "\n".join(ln.strip() for ln in t.splitlines())
    return t