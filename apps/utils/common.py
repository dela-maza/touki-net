def to_zenkaku_digits(s: str) -> str:
    """半角数字(0-9)を全角数字(０-９)に変換する"""
    table = str.maketrans("0123456789", "０１２３４５６７８９")
    return s.translate(table)