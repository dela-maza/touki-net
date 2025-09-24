# apps/______register/services/commerce/services.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from apps.shared.wareki import z2h, normalize_number, wareki_to_iso
from .patterns import (
    RE_CORPORATE_NUMBER, RE_COMPANY_NAME, RE_HEAD_OFFICE,
    RE_PURPOSE_HEAD, RE_PURPOSE_LINE, RE_PUBLIC_NOTICE,
    RE_CAPITAL, RE_AUTHORIZED_SHARES, RE_TRANSFER_RESTRICTION,
    RE_OFFICER_LINE, RE_RECEIPT, RE_RECEIPT_DATE, RE_RECEIPT_NUMBER
)

# --- 任意: Enum があれば使う。無くても動くようにフォールバック ---
try:
    # あなたの環境で method 化している（from_text / to_labels を持つ）想定
    from apps.______register.constants.organization_type import OrganizationType
    _HAS_ORG_ENUM = True
except Exception:
    OrganizationType = None
    _HAS_ORG_ENUM = False


# 罫線・縦棒・全角スペース等をザックリ落とす（見出し検出を安定させる）
_BOX_CHARS = str.maketrans({
    "│": " ",
    "┃": " ",
    "｜": " ",  # 全角縦棒
    "—": "-",
    "─": "-",
    "━": "-",
    "┆": " ",
    "┊": " ",
    # 必要に応じて追加
})
_FULLWIDTH_SPACE = "　"


# 追加：罫線・区切り候補の検出（raw_line を見る）
_DIVIDER_RE = re.compile(r"[┏┓┗┛┣┫┳┻┠┨┯┷━─]{2,}")

def _is_divider(raw_line: str) -> bool:
    """箱線/罫線っぽい行か？（区切りとみなす）"""
    if not raw_line:
        return False
    # 罫線記号の並び、または罫線記号＋スペース中心の行
    if _DIVIDER_RE.search(raw_line):
        return True
    # 8割以上が罫線/空白なら divider 扱い
    t = raw_line.strip()
    if not t:
        return False
    only_box = re.sub(r"[┏┓┗┛┣┫┳┻┠┨┯┷━─\s]+", "", t)
    return len(only_box) <= max(1, int(len(t) * 0.2))

def _preclean(s: str) -> str:
    """
    PDF テキスト（OCR/抽出済）から、箱線や縦棒、余計な全角空白の
    塊を除去/圧縮して検索しやすくする
    """
    if not s:
        return ""
    s = s.translate(_BOX_CHARS)
    # 連続全角スペースを半角1つに潰す
    s = s.replace(_FULLWIDTH_SPACE, " ")
    s = _squash_spaces(s)
    return s


def _squash_spaces(s: str) -> str:
    # 連続スペースを1つに
    return re.sub(r"[ \t]+", " ", s).strip()


def _pick_after_label(line: str, label_pattern: re.Pattern) -> Optional[str]:
    """
    1行から 「<ラベル> : 値」 を取り出すヘルパ。
    例: 「商　号 ： 株式会社ティアテック」 → 「株式会社ティアテック」
    """
    m = label_pattern.search(line)
    if not m:
        return None
    # パターンは (ラベル)(値) の順で作ってある想定（RE_COMPANY_NAME など）
    # group(2) が値
    val = (m.group(2) or "").strip()
    # 値の末尾に残る埋め草スペース/点線等を軽く削る
    val = re.sub(r"[-・.]+$", "", val).strip()
    return val or None


class CommerceRegisterParser:
    """
    OCR/抽出済みテキストから商業登記（全部事項）を“ざっくり堅めに”構造化。
    - 会社法人等番号
    - 商号/名称
    - 本店/主たる事務所
    - 目的（複数行）
    - 公告方法
    - 資本金
    - 発行可能株式総数
    - 株式の譲渡制限に関する規定
    - 役員（代表/その他）
    - 受付（年月日・番号）  ※見つかった範囲で
    """

    def parse_text(self, text: str) -> Dict[str, Any]:
        # 前処理：行単位＋罫線除去・空白圧縮
        raw_lines = (text or "").splitlines()
        lines: List[str] = [_preclean(l) for l in raw_lines if _preclean(l)]
        full_text = "\n".join(lines)

        data: Dict[str, Any] = {
            "organization_type": "",            # KK/GK/... のコード
            "organization_type_label_ja": "",   # 例: 株式会社
            "organization_type_label_en": "",   # 例: Joint-Stock Company
            "raw_name": "",                     # 登記上の名称（前株/後株を含めそのまま）
            "company_number": "",               # 会社法人等番号
            "head_office": "",                  # 本店/主たる事務所
            "purposes": [],                     # 目的（配列）
            "public_notice": "",                # 公告方法
            "capital_jpy": None,                # 資本金（int）
            "authorized_shares": None,          # 発行可能株式総数（int）
            "transfer_restriction": "",         # 株式の譲渡制限
            "representatives": [],              # 代表者 [{title, name}]
            "officers": [],                     # その他役員 [{title, name}]
            "receipt": {
                "raw": "",
                "date": None,                   # YYYY-MM-DD（和暦→ISO 変換）
                "number": None,                 # 受付番号
            },
        }

        # --- 会社法人等番号 ---
        if m := RE_CORPORATE_NUMBER.search(full_text):
            num = z2h(m.group(2))
            data["company_number"] = num

        # --- 商号 / 名称（全角スペース/縦線混じりにも比較的強い） ---
        for l in lines:
            name = _pick_after_label(l, RE_COMPANY_NAME)
            if name:
                data["raw_name"] = name
                self._infer_org_type(data, name)
                break

        # --- 本店 / 主たる事務所 ---
        for l in lines:
            office = _pick_after_label(l, RE_HEAD_OFFICE)
            if office:
                data["head_office"] = office
                break

        # --- 目的 ---
        purposes: List[str] = []

        # 目的見出しの行番号を探す（clean後の行で）
        head_idx: Optional[int] = None
        for i, l in enumerate(lines):
            if RE_PURPOSE_HEAD.search(l):
                head_idx = i
                break

        if head_idx is not None:
            # 見出しの次行から raw_lines/lines を並行走査
            i = head_idx + 1
            while i < len(lines):
                raw_l = raw_lines[i]         # 生行（罫線検出用）
                clean_l = lines[i]           # 正規化済み（抽出用）

                # 罫線/区切りに遭遇 → 目的ブロック終了
                if _is_divider(raw_l):
                    break

                # 空行はスキップ（段落の境界だが目的本文の一部なこともある）
                if not clean_l.strip():
                    i += 1
                    continue

                # 箇条書き（・/一/1/（1）…）を緩く許容
                if RE_PURPOSE_LINE.match(clean_l) or re.match(r"^[(（]?\s*[一1１]\s*[)）.]?\s*(.+)", clean_l):
                    item = re.sub(r"^・?\s*", "", clean_l).strip()
                    if item:
                        purposes.append(item)
                else:
                    # 行継続とみなして直前項目に追記（折返し対策）
                    if purposes:
                        purposes[-1] = (purposes[-1] + " " + clean_l.strip()).strip()
                    else:
                        purposes.append(clean_l.strip())

                i += 1

            data["purposes"] = [p for p in purposes if p]

            # --- 公告方法 ---
            if m := RE_PUBLIC_NOTICE.search(full_text):
                data["public_notice"] = _squash_spaces(m.group(2))

            # --- 資本金 ---
            if m := RE_CAPITAL.search(full_text):
                data["capital_jpy"] = int(normalize_number(m.group(2)))

            # --- 発行可能株式総数 ---
            if m := RE_AUTHORIZED_SHARES.search(full_text):
                data["authorized_shares"] = int(normalize_number(m.group(2)))

            # --- 株式の譲渡制限 ---
            if m := RE_TRANSFER_RESTRICTION.search(full_text):
                data["transfer_restriction"] = _squash_spaces(m.group(2))

            # --- 役員（代表/その他） ---
            for l in lines:
                if m := RE_OFFICER_LINE.search(l):
                    title = _squash_spaces(m.group(1))
                    name = _squash_spaces(m.group(2))
                    row = {"title": title, "name": name}
                    if "代表" in title:
                        data["representatives"].append(row)
                    else:
                        data["officers"].append(row)

            # --- 受付情報（あれば） ---
            if m := RE_RECEIPT.search(full_text):
                raw = m.group(0)
                data["receipt"]["raw"] = raw
                if d := RE_RECEIPT_DATE.search(raw):
                    data["receipt"]["date"] = wareki_to_iso(d.group(0))  # 和暦→ISO
                if n := RE_RECEIPT_NUMBER.search(raw):
                    data["receipt"]["number"] = z2h(n.group(1))

            return data

    # -------------------------
    # 内部：組織種別の推定（Enum があればそれを利用）
    # -------------------------
    def _infer_org_type(self, data: Dict[str, Any], name: str) -> None:
        t = name or ""

        if _HAS_ORG_ENUM:
            # あなたの OrganizationType が classmethod を持つ前提
            try:
                org = OrganizationType.from_text(t)  # type: ignore[attr-defined]
            except Exception:
                org = None
            if org:
                try:
                    labels = org.to_labels()  # type: ignore[attr-defined]
                    data["organization_type"] = labels.get("code", "") or getattr(org, "value", "")
                    data["organization_type_label_ja"] = labels.get("ja", "")
                    data["organization_type_label_en"] = labels.get("en", "")
                    return
                except Exception:
                    # 失敗したらフォールバックに落ちる
                    pass

        # --- フォールバック（Enumなし/失敗時） ---
        code = ja = en = ""
        if "株式会社" in t:
            code, ja, en = "KK", "株式会社", "Joint-Stock Company"
        elif "有限会社" in t:
            code, ja, en = "YK", "有限会社", "Limited Company (Yugen)"
        elif "合同会社" in t:
            code, ja, en = "GK", "合同会社", "LLC (Godo Kaisha)"
        elif "一般社団法人" in t:
            code, ja, en = "SHADAN", "一般社団法人", "General Incorporated Association"

        data["organization_type"] = code
        data["organization_type_label_ja"] = ja
        data["organization_type_label_en"] = en

    # 便利：JSON 文字列で返す
    def parse_text_to_json(self, text: str, *, ensure_ascii: bool = False, indent: int = 2) -> str:
        data = self.parse_text(text)
        return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)