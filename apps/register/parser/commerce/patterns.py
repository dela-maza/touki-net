# apps/register/parser/commerce/patterns.py

import re

RE_CORPORATE_NUMBER = re.compile(r"(会社法人等番号)[:：]?\s*([0-9０-９]{12,13})")
RE_COMPANY_NAME = re.compile(r"(商号|名称)[:：]?\s*(.+)")
RE_HEAD_OFFICE = re.compile(r"(本店|主たる事務所)[:：]?\s*(.+)")
RE_PURPOSE_HEAD = re.compile(r"目的[:：]?\s*$")
RE_PURPOSE_LINE = re.compile(r"^・?\s*(.+)")
RE_PUBLIC_NOTICE = re.compile(r"(公告をする方法)[:：]?\s*(.+)")
RE_CAPITAL = re.compile(r"(資本金の額)[:：]?\s*([0-9,０-９，]+)\s*円")
RE_AUTHORIZED_SHARES = re.compile(r"(発行可能株式総数)[:：]?\s*([0-9,０-９，]+)\s*株")
RE_TRANSFER_RESTRICTION = re.compile(r"(株式の譲渡制限に関する規定)[:：]?\s*(.+)")

# 役員（代表取締役/取締役/代表社員/理事 等）
RE_OFFICER_LINE = re.compile(
    r"(代表取締役|取締役|監査役|代表社員|業務執行社員|理事|代表理事)[\s　]*[:：]?\s*([^（(]+)"
)

# 登記受付
RE_RECEIPT = re.compile(r"(受付|受付年月日)[:：]?\s*(令和|平成|昭和)?[0-9０-９/年月日.\- ]+第[0-9０-９]+号")
RE_RECEIPT_DATE = re.compile(r"(令和|平成|昭和)?[0-9０-９]+年[0-9０-９]+月[0-9０-９]+日")
RE_RECEIPT_NUMBER = re.compile(r"第\s*([0-9０-９]+)\s*号")