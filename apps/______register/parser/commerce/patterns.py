# apps/______register/services/commerce/patterns.py
import re

# 共通の“区切り”表現
SEP = r"(?:[:：|])"

# 「行頭 or 縦線の直後」→ ラベル → 区切り → 値 → 「縦線 or 行末」
RE_COMPANY_NAME = re.compile(rf"(?:^|\|)\s*(?:商号|名称)\s*{SEP}?\s*(.+?)(?:\s*\||$)")
RE_HEAD_OFFICE  = re.compile(rf"(?:^|\|)\s*(?:本店|主たる事務所)\s*{SEP}?\s*(.+?)(?:\s*\||$)")

# 会社法人等番号は桁区切りや空白が混ざる想定で緩めに取り、後で数字だけに詰める
RE_CORPORATE_NUMBER = re.compile(rf"(?:^|\|)\s*会社法人等番号\s*{SEP}?\s*([0-9\s]{{12,16}})(?:\s*\||$)")

# 目的のヘッダ行（末尾が値無しで終わる想定）
RE_PURPOSE_HEAD = re.compile(rf"(?:^|\|)\s*目的\s*{SEP}?\s*$")
# 箇条書きの行。先頭に「・」「-」「(1)」「１.」「一、」など来ても拾う
RE_PURPOSE_LINE = re.compile(r"^\s*(?:・|-|・?第?\d+[.)、]?|[一二三四五六七八九十]+[、.)]?)\s*(.+)")

RE_PUBLIC_NOTICE = re.compile(rf"(?:^|\|)\s*公告をする方法\s*{SEP}?\s*(.+?)(?:\s*\||$)")
RE_CAPITAL = re.compile(rf"(?:^|\|)\s*資本金の額\s*{SEP}?\s*([0-9,]+)\s*円")
RE_AUTHORIZED_SHARES = re.compile(rf"(?:^|\|)\s*発行可能株式総数\s*{SEP}?\s*([0-9,]+)\s*株")
RE_TRANSFER_RESTRICTION = re.compile(rf"(?:^|\|)\s*株式の譲渡制限に関する規定\s*{SEP}?\s*(.+?)(?:\s*\||$)")

# 役員（代表取締役/取締役/代表社員/理事 等）: 「役職 [区切り] 氏名（括弧は除外）」想定
RE_OFFICER_LINE = re.compile(
    rf"(?:^|\|)\s*(代表取締役|取締役|監査役|代表社員|業務執行社員|理事|代表理事)\s*{SEP}?\s*([^（(｜|]+)"
)

# 受付（元号＋日付＋第○号）を丸ごと拾う版＋日付/番号を個別で抽出する補助
RE_RECEIPT      = re.compile(r"(?:受付|受付年月日)\s*[:：|]?\s*([令和平成昭和大正明治]?\s*\d+年\d+月\d+日).*?第\s*([0-9０-９]+)\s*号")
RE_RECEIPT_DATE = re.compile(r"([令和平成昭和大正明治])\s*([0-9０-９]+)年\s*([0-9０-９]+)月\s*([0-9０-９]+)日")
RE_RECEIPT_NUMBER = re.compile(r"第\s*([0-9０-９]+)\s*号")