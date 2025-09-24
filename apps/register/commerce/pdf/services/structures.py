# apps/register/commerce/pdf/services/structures.py
from __future__ import annotations
import re
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# 商業登記規則 別表５に基づく「登記事項の区分」を Enum として定義
class RegistrySectionType(Enum):
    COMPANY_INFO = "会社情報区"  # 商号区に含まれる情報（法人番号、商号、本店、公告方法など）
    PURPOSE = "目的区"  # 会社の目的
    CAPITAL = "株式・資本区"  # 資本金・株式関連
    OFFICERS = "役員区"  # 取締役・監査役・清算人など
    OFFICER_RESPONSIBILITY = "役員責任区"  # 責任免除・制限
    MANAGER = "会社支配人区"  # 支配人
    BRANCH = "支店区"  # 支店
    WARRANT = "新株予約権区"  # 新株予約権
    HISTORY = "会社履歴区"  # 合併・分割などの歴史的事項
    ENTERPRISE_MORTGAGE = "企業担保権区"  # 企業担保権
    STATUS = "会社状態区"  # 存続期間・解散・破産等
    RECORD = "登記記録区"  # 登記記録そのもの（起因・閉鎖）


@dataclass(frozen=True)
class LabelPattern:
    """
    1つの「ラベル（見出し）」を識別するための正規表現パターン。

    例:
        - "商号" → r"^商号$|^商号区$|^商\s*号$"
        - "本店" → r"本店(の所在場所|所在地)?|^本\s*店$"
    """

    pattern: str  # LabelPattern(r"会社法人等番号")等で、インスタンス化した際に、代入される

    def matches(self, text: str) -> bool:
        """
        与えられた文字列（title や label）とこのパターンがマッチするかどうかを返す。
        空白・全角スペースなどを取り除いて正規化してから検索する。
        """
        normalized = re.sub(r"\s+", "", text or "")
        return re.search(self.pattern, normalized) is not None


@dataclass
class SectionCatalog:
    """
    「どの RegistrySectionType（親区分）に属するか」を判定するカタログ。

    - table: RegistrySectionType -> List[LabelPattern]
      各区分ごとに、その区分に属するラベル候補を正規表現で保持する。
    """

    table: Dict[RegistrySectionType, List[LabelPattern]] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "SectionCatalog":
        """
        デフォルトのカタログを生成する。
        商業登記規則・別表５に出てくる項目を中心に、
        実際の登記事項証明書に登場するラベルを正規表現でカバーしている。
        """
        return cls(
            table={
                RegistrySectionType.COMPANY_INFO: [
                    LabelPattern(r"会社法人等番号"),
                    LabelPattern(r"^商号$|^商号区$|^商\s*号$"),
                    LabelPattern(r"本店(の所在場所|所在地)?|^本\s*店$"),
                    LabelPattern(r"電子提供措置の定め"),
                    LabelPattern(r"公告(をする)?方法|^公告$"),
                    LabelPattern(r"貸借対照表.*提供.*必要な事項"),
                    LabelPattern(r"中間貸借対照表.*提供.*必要な事項"),
                    LabelPattern(r"会社成立の年月日"),
                ],
                RegistrySectionType.PURPOSE: [
                    LabelPattern(r"^目[ 　]?的$"),
                ],
                RegistrySectionType.CAPITAL: [
                    LabelPattern(r"単元株式数"),
                    LabelPattern(r"発行可能株式総数"),
                    LabelPattern(r"発行済株式の総数(並びに種類及び数)?"),
                    LabelPattern(r"株券(を発行する旨|発行会社である旨)"),
                    LabelPattern(r"資本金の額"),
                    LabelPattern(r"発行する株式の内容"),
                    LabelPattern(r"発行可能種類株式総数"),
                    LabelPattern(r"各種類の株式の内容"),
                    LabelPattern(r"株主名簿管理人.*氏名.*住所.*営業所"),
                    LabelPattern(r"創立費の償却の方法"),
                    LabelPattern(r"事業費の償却の方法"),
                    LabelPattern(r"その他株式又は資本金に関する事項"),
                ],
                RegistrySectionType.OFFICERS: [
                    LabelPattern(r"取締役|仮取締役|取締役職務代行者"),
                    LabelPattern(r"監査等委員である取締役"),
                    LabelPattern(r"会計参与|仮会計参与|会計参与職務代行者"),
                    LabelPattern(r"計算書類等の備置き場所"),
                    LabelPattern(r"監査役|仮監査役|監査役職務代行者"),
                    LabelPattern(r"代表取締役|仮代表取締役|代表取締役職務代行者"),
                    LabelPattern(r"特別取締役"),
                    LabelPattern(r"委員|委員職務代行者"),
                    LabelPattern(r"執行役|代表執行役"),
                    LabelPattern(r"会計監査人|仮会計監査人"),
                    LabelPattern(r"社外取締役である旨"),
                    LabelPattern(r"社外監査役である旨"),
                    LabelPattern(r"清算人|仮清算人|清算人職務代行者|代表清算人"),
                    LabelPattern(r"監査役の監査の範囲.*会計に限定.*定款の定め"),
                    LabelPattern(r"職務の執行停止"),
                    LabelPattern(r"その他役員等に関する事項"),
                ],
                # （以下も同様に…省略）
            }
        )

    def detect_parent(self, title_or_label: str) -> Optional[RegistrySectionType]:
        """
        ラベル/タイトルから親の区を推定して返す。
        例:
            "商号"   → COMPANY_INFO
            "本店"   → COMPANY_INFO
            "取締役" → OFFICERS
        """
        # self.table は {RegistrySectionType: [LabelPattern, ...]} の辞書。
        # 各区分（例: COMPANY_INFO, OFFICERS）ごとに、対応する正規表現パターンのリストを持っている。
        for sec_type, patterns in self.table.items():
            # その区分に登録された全パターンを走査して、
            # 引数の title_or_label が どれか1つでもマッチすれば、その sec_type を返す。
            if any(p.matches(title_or_label) for p in patterns):
                return sec_type

        # どの区分のパターンにもマッチしなければ None を返す（未分類）
        return None


@dataclass
class Line:
    text: str

    def __str__(self) -> str:
        return self.text

    def parse_cells(self):
        """
        '┃ … │ … │ … ┃' を (label, value, tail) の3要素に分解。
        """
        t = self.text.strip("┃ ").rstrip("┃ ").strip()
        parts = [p.strip() for p in t.split("│")]
        label = parts[0] if len(parts) >= 1 else None
        value = parts[1] if len(parts) >= 2 else None
        tail = parts[2] if len(parts) >= 3 else None
        return (label, value, tail)

    def to_dict(self) -> dict:
        label, value, tail = self.parse_cells()
        return {
            "label": label,
            "value": value,
            "tail": tail,
            "raw": self.text,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class EntryBlock:
    """
    変更ありの3行セットなど “複数行で1意味” の塊を保持。
    lines は順に [先頭/本体, 中間(例:『番』), 末尾(例:『令和…登記』)] を想定
    """
    BOX_GLYPHS = "━─│┏┓┗┛┠┨┿┯┷┳┻┼┬┴├┤"

    lines: List[Line]

    def to_dict(self) -> dict:
        return {"lines": [str(ln) for ln in self.lines]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @property
    def merged_line(self) -> Line:
        """
        表示・解析用に1行へ正規化して返す。
        例)
            ┃ │ 東京都…1028 │令和…移転┃
            ┃ │ 番 ├-------------┨
            ┃ │ │令和…登記┃
                    ↓
            ┃ │東京都…1028番 │ 令和…移転 令和…登記 ┃
        """

        def _is_box_only(s: str) -> bool:
            s = s.strip()
            return bool(s) and all(ch in self.BOX_GLYPHS for ch in s)

        def _strip_bars(s: str) -> str:
            # 両端の「┃」や余計な空白を除去
            return s.strip().lstrip("┃").rstrip("┃").strip()

        def _split_3cells(s: str) -> list[str]:
            # 「│」で分割して3セルに揃える（足りない分は空文字）
            parts = [p.strip() for p in s.split("│")]
            return (parts + ["", "", ""])[:3]

        col = ["", "", ""]  # label, value, tail の蓄積

        for ln in self.lines:
            raw = ln.text.strip()
            if not raw or _is_box_only(raw):
                continue

            s = _strip_bars(raw)
            c0, c1, c2 = _split_3cells(s)

            col[0] += c0
            col[1] += c1
            col[2] += c2

        # 必ず3セルの形で返す（ラベルが空でもOK）
        return Line(f"┃ {col[0]} │ {col[1]} │ {col[2]} ┃")


@dataclass
class HistoryRecord:
    """
    登記事項の履歴を保持するクラス。

    - registered_matter: 登記事項欄に記載される内容（住所、役員名など）
    - date: 原因日付 or 登記日付（現在は区別せず文字列で保持）
    """
    registered_matter: str
    date: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "registered_matter": self.registered_matter,
            "date": self.date
        }

    def __str__(self) -> str:
        return f"{self.registered_matter} ({self.date})" if self.date else self.registered_matter


@dataclass
class RegistryItem:
    entry_blocks: List[EntryBlock]

    @property
    def item_key(self) -> Optional[str]:
        if not self.entry_blocks:
            return None
        label, _, _ = self.entry_blocks[0].lines[0].parse_cells()
        return label

    @property
    def current_value(self) -> Optional[str]:
        if not self.entry_blocks:
            return None
        merged = self.entry_blocks[-1].merged_line
        _, value, extra = merged.parse_cells()
        return f"{value}{extra or ''}"

    def history(self) -> List["HistoryRecord"]:
        results: List[HistoryRecord] = []
        for entry_block in self.entry_blocks:
            merged = entry_block.merged_line
            _, registered_matter, date = merged.parse_cells()
            results.append(HistoryRecord(registered_matter=registered_matter or "", date=date))
        return results

    def to_dict(self) -> dict:
        return {
            "key": self.item_key,
            "current_value": self.current_value,
            "history": [h.to_dict() for h in self.history()],
            "blocks": [b.to_dict() for b in self.entry_blocks],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class RegistrySection:
    raw_text: str
    title: str
    # ↓ 命名を items に統一（読みやすい）
    items: List[RegistryItem]

    def values(self) -> Dict[str, Optional[str]]:
        return {item.item_key: item.current_value for item in self.items if item.item_key}

    # ↓ 戻り型を HistoryRecord に合わせる
    def histories(self) -> Dict[str, List[HistoryRecord]]:
        return {item.item_key: item.history() for item in self.items if item.item_key}

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "values": self.values(),
            # ↓ JSONに載せる時は dict 化して可読性アップ
            "histories": {k: [h.to_dict() for h in v] for k, v in self.histories().items()},
            "items": [it.to_dict() for it in self.items],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
