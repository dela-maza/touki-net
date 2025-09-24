# -*- coding: utf-8 -*-
"""
株式会社の登記簿（全部事項）PDF → JSON構造化 抽出スクリプト（コメント厚め版）

目的：
- 登記簿の主要セクション（商号／本店／公告方法／会社成立／目的／発行可能株式総数／発行済株式／資本金／譲渡制限／役員／登記記録）を抽出
- 変更がある場合、「新旧（old/new）」と「効力発生日／登記日」を含む履歴（history）を保持
- 和暦→ISO日付、全角→半角、数値（万・億・円・株）の正規化に対応
- PDFの版面ゆらぎに耐えるよう、「正規化→セクション分割→各セクション専用パーサ」という段階設計

設計上の重要点：
- まず「正規化（ノイズ除去・空白折り畳み）」で抽出の安定性を確保
- セクションは「見出し語の出現位置」をマークし、次見出し直前までを当該セクションとして切出す
- 「本店」の履歴は、住所行＋（移転／登記）行のペアを時系列で復元して current と history を構築
- 役員は「住所候補→役職＋氏名→イベント行」を状態機械的にグルーピング
- 数値と日付は汎用関数で統一変換し、JSONには raw も残す（再現性確保）

使い方：
    python parse_kabushiki_registry.py /path/to/xxx.pdf -o /path/to/out.json

依存（少なくともどれか一つが入っていればOK）：
    PyPDF2 / pdfminer.six / pdfplumber
"""

from __future__ import annotations
import re
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

# =========================
# 1) PDFテキスト抽出（3段フォールバック）
# =========================
def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    PDF→テキストの抽出。
    - まず PyPDF2（軽量・速い）を試し、ダメなら pdfminer（強力）、最後に pdfplumber（表に強い）を試す。
    - いずれでも失敗したら空文字を返す（呼び出し側で判定）。
    """
    text = ""
    # (a) PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n".join(pages)
    except Exception:
        pass

    # (b) pdfminer
    if not text.strip():
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(str(pdf_path))
        except Exception:
            pass

    # (c) pdfplumber
    if not text.strip():
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf_path)) as pdf:
                pages = []
                for page in pdf.pages:
                    pages.append(page.extract_text() or "")
                text = "\n".join(pages)
        except Exception:
            pass
    return text or ""


# =========================
# 2) 正規化（ノイズ除去・空白折り畳み）
# =========================
BOX_CHARS = "━─│┏┓┗┛┠┨┿┯┷┳┻"
ZEN2HAN = str.maketrans("０１２３４５６７８９－，", "0123456789-,")  # 全角→半角

def normalize_text(t: str) -> str:
    """
    正規化の狙い：
      - PDF抽出の表罫線や装飾（ボックス文字）を除去
      - 全角空白→半角、連続空白の圧縮
      - 行末・行頭の無駄空白トリム
      - これにより後続の正規表現の当たりを良くする
    """
    t = t.replace("\u3000", " ")                    # 全角空白→半角
    t = re.sub(f"[{BOX_CHARS}]+", "", t)            # 罫線類の除去
    t = t.replace("┃", " ").replace("│", " ").replace("｜", " ")  # 縦線類の除去
    t = re.sub(r"[ \t]+", " ", t)                   # 連続空白の圧縮
    t = "\n".join(ln.strip() for ln in t.splitlines())  # 行単位トリム
    return t


# =========================
# 3) 和暦→ISO日付、数値正規化
# =========================
ERA_BASE = {"令和": 2018, "平成": 1988, "昭和": 1925}

def wareki_to_date_str(s: str) -> Optional[str]:
    """
    和暦（令和/平成/昭和）表現をざっくり抽出して ISO (YYYY-MM-DD) に変換。
    例: "令和 5 年 10 月 16 日変更" → "2023-10-16"
    - 数字は全角混在のため、先に半角化
    - （注意）複数日付が同一行にある場合は最初にマッチしたものを採用（必要なら拡張）
    """
    s2 = s.translate(ZEN2HAN)
    m = re.search(r"(令和|平成|昭和)\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日", s2)
    if not m:
        return None
    era, y, mo, d = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    if era not in ERA_BASE:
        return None
    year = ERA_BASE[era] + y  # 例：令和1年＝2019年 → 2018 + 1 = 2019
    return f"{year:04d}-{mo:02d}-{d:02d}"


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


# =========================
# 4) メタ情報：as_of・法人番号・会社名など
# =========================
def parse_metadata(norm: str) -> Dict[str, Any]:
    """
    文書ヘッダなどからメタを拾えるだけ拾う。
    - as_of: 「YYYY/MM/DD HH:MM 現在の情報です」
    - corporate_number: 「会社法人等番号 XXXXX-XX-XXXXXX」
    - company_name: 「商号」セクションからも取るが、先に拾えるなら拾っておく
    """
    meta: Dict[str, Any] = {}

    # 例：２０２４／１０／０２ １３：４７ 現在の情報です
    m = re.search(r"(\d{4})[／/](\d{2})[／/](\d{2})\s+(\d{2})：?(\d{2}).*現在の情報です", norm)
    if m:
        meta["as_of"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}"

    # 会社法人等番号
    m = re.search(r"会社法人等番号\s*([0-9０-９\-－]+)", norm)
    if m:
        meta["corporate_number"] = m.group(1).translate(ZEN2HAN)

    # 商号（会社名）は後のセクションでより確実に拾うが、ここで取れれば暫定格納
    m = re.search(r"\n商\s*号\s*(.+?)(?:\n|$)", norm)
    if m:
        meta["company_name"] = re.sub(r"\s+", " ", m.group(1)).strip()
    return meta


# =========================
# 5) セクション分割（見出し語ベース）
# =========================
SECTION_KEYS = [
    "商号", "本店", "公告をする方法", "会社成立の年月日", "目的",
    "発行可能株式総数", "発行済株式の総数", "資本金の額",
    "株式の譲渡制限に関する規定", "役員に関する事項", "登記記録に関する事項"
]

def split_sections(norm: str) -> Dict[str, str]:
    """
    セクションの始点（見出し語の出現位置）を列挙し、次の見出し直前までを当該セクションとして切り出す。
    - 表の崩れで見出し語が複数回出る場合があるため、複数ヒットも許容
    - 最後のセクションは文末まで
    """
    positions = []
    for key in SECTION_KEYS:
        for m in re.finditer(rf"\n{re.escape(key)}\s", norm):
            positions.append((m.start(), key))
    positions.sort()

    sections: Dict[str, str] = {}
    for i, (pos, key) in enumerate(positions):
        end = positions[i+1][0] if i + 1 < len(positions) else len(norm)
        sections[key] = norm[pos:end]
    return sections


# =========================
# 6) 各セクション用パーサ（商号・公告・設立・目的・株式・資本・譲渡制限・本店・役員・登記記録）
# =========================
def parse_trade_name(sec: str) -> Dict[str, Any]:
    """
    商号（会社名）
    - 見出し行は改行をまたぎやすいので、最初の2行程度を合体して正規表現。
    - 履歴（商号変更）は登記簿の別位置に出ることが多く、ここでは current のみ。必要なら拡張。
    """
    line = " ".join(sec.splitlines()[0:2])      # 最初の2行を弱結合
    m = re.search(r"商\s*号\s*(.+)$", line)
    current = m.group(1).strip() if m else ""
    return {"current": current, "history": []}  # historyは別セクションで拡張可能


def parse_public_notice(sec: str) -> str:
    m = re.search(r"公告をする方法\s*(.+)", sec)
    return m.group(1).strip() if m else ""


def parse_incorporation_date(sec: str) -> Optional[str]:
    m = re.search(r"会社成立の年月日\s*([^\n]+)", sec)
    return wareki_to_date_str(m.group(1)) if m else None


def parse_purposes(sec: str) -> Dict[str, Any]:
    """
    目的（自由文＋箇条書き）。
    - 箇条書きを「行頭の番号（1.／①〜）」やインデントで検出し、itemsに詰める。
    - 必要に応じて同義語統合は後段で実施（ここでは生テキストを保持）。
    """
    body = "\n".join(sec.splitlines()[1:]).strip()
    items: List[str] = []
    for ln in body.splitlines():
        if re.search(r"^\d+[．\.、]?\s", ln) or re.search(r"^①|^②|^③|^④|^⑤|^⑥|^⑦|^⑧|^⑨|^⑩", ln):
            items.append(re.sub(r"\s+", " ", ln).strip())
        elif items and (ln.startswith("　") or ln.startswith(" ")*2):
            # 直前項目の続き（インデントによる小項目）を連結
            items[-1] = items[-1] + " " + re.sub(r"\s+", " ", ln).strip()
    return {"items": items}


def parse_authorized_shares(sec: str) -> Dict[str, Any]:
    m = re.search(r"発行可能株式総数\s*([^\n]+)", sec)
    raw = m.group(1).strip() if m else ""
    val = jp_amount_to_int(raw)
    return {"raw": raw, "value": val}


def parse_issued_shares(sec: str) -> Dict[str, Any]:
    """
    「発行済株式の総数（並びに種類及び数）」のように見出し語が長いことがあるので、
    行送りを跨いで最初の本文行を取得
    """
    m = re.search(r"発行済株式の総数[^\n]*\n?\s*([^\n]+)", sec)
    raw = (m.group(1).strip() if m else "").replace("並びに種類及び数", "").strip()
    val = jp_amount_to_int(raw)
    return {"raw": raw, "value": val}


def parse_capital(sec: str) -> Dict[str, Any]:
    m = re.search(r"資本金の額\s*([^\n]+)", sec)
    raw = m.group(1).strip() if m else ""
    val = jp_amount_to_int(raw)  # 「金800万円」→ 8_000_000
    return {"raw": raw, "value_jpy": val}


def parse_transfer_restrictions(sec: str) -> str:
    m = re.search(r"株式の譲渡制限に関する規定\s*(.+)", sec)
    return m.group(1).strip() if m else ""


def parse_head_office(sec: str) -> Dict[str, Any]:
    """
    本店（current + history）
    - 住所行（都/道/府/県〜）を拾い、その直後〜近接行で「移転／登記」日付を紐付ける。
    - 収集した「住所＋日付」レコードを日付でソートし、old→new の履歴を構築。
    """
    lines = [ln for ln in sec.splitlines() if ln.strip()]
    moves: List[Dict[str, Any]] = []
    pending_addr = None  # 直近の住所バッファ

    for ln in lines[1:]:
        # 住所候補（かなり緩めのヒューリスティック：都道府県～市区郡町村を含むか）
        if re.search(r"(都|道|府|県).+(市|区|郡|町|村)", ln) and not re.search(r"(就任|辞任|更正|登記|移転)", ln):
            pending_addr = re.sub(r"\s+", " ", ln).strip()
            continue

        # 「移転」「登記」などのイベント行
        if "移転" in ln or "登記" in ln:
            eff = wareki_to_date_str(ln) if "移転" in ln else None
            reg = wareki_to_date_str(ln) if "登記" in ln else None
            if pending_addr:
                # 直近住所にイベントをひも付ける。既存レコードがなければ新規作成。
                rec = next((x for x in moves if x.get("new") == pending_addr), None)
                if not rec:
                    rec = {"new": pending_addr, "effective_date": None, "registration_date": None, "event": "移転"}
                    moves.append(rec)
                if eff:
                    rec["effective_date"] = eff
                if reg:
                    rec["registration_date"] = reg

    # 日付で時系列に並べる（effective_date→registration_date の順で優先）
    def sort_key(x):
        return (x.get("effective_date") or x.get("registration_date") or "9999-99-99")
    moves_sorted = sorted(moves, key=sort_key)

    # 履歴（old→new）
    history: List[Dict[str, Any]] = []
    for i in range(1, len(moves_sorted)):
        old = moves_sorted[i-1].get("new")
        new = moves_sorted[i].get("new")
        history.append({
            "old": old,
            "new": new,
            "effective_date": moves_sorted[i].get("effective_date"),
            "registration_date": moves_sorted[i].get("registration_date"),
            "event": moves_sorted[i].get("event", "移転"),
        })

    current = moves_sorted[-1]["new"] if moves_sorted else ""
    return {"current_address": current, "history": history}


def parse_officers(sec: str) -> List[Dict[str, Any]]:
    """
    役員（代表取締役・取締役・監査役など）
    - 住所→役職＋氏名→イベント（就任・退任・辞任・更正・住所移転・登記）の順に並ぶ版面を想定
    - 住所は直前行のバッファに保持→次の「役職＋氏名」に結びつける
    - イベントは ISO 日付化して events[] に積む
    """
    lines = [ln for ln in sec.splitlines() if ln.strip()]
    officers: List[Dict[str, Any]] = []
    current_officer: Optional[Dict[str, Any]] = None
    last_address: Optional[str] = None

    ROLE_PAT = r"(代表取締役|取締役|監査役|会計参与|清算人)"
    for ln in lines[1:]:
        # 住所っぽい行（番・号・丁目・階・F などを軽く指標に）
        if re.search(r"(都|道|府|県).+(市|区|郡|町|村).*(番|号|丁目|F|階)", ln) and not re.search(ROLE_PAT, ln):
            last_address = re.sub(r"\s+", " ", ln).strip()
            continue

        # 役職＋氏名の行
        m = re.search(rf"{ROLE_PAT}\s+(.+)", ln)
        if m:
            # 直前の officer があれば push
            if current_officer:
                officers.append(current_officer)
            role = m.group(1)
            name = re.sub(r"\s+", " ", m.group(2)).strip()
            current_officer = {"role": role, "name": name, "address": last_address, "events": []}
            last_address = None
            continue

        # イベント（日付＋キーワード）
        if re.search(r"(就任|退任|辞任|更正|住所移転|登記)", ln):
            date = wareki_to_date_str(ln)
            event = None
            for key in ["就任", "退任", "辞任", "更正", "住所移転", "登記"]:
                if key in ln:
                    event = key
                    break
            if current_officer and event and date:
                current_officer["events"].append({"event": event, "date": date})
            continue

    if current_officer:
        officers.append(current_officer)
    return officers


def parse_registration_notes(sec: str) -> List[Dict[str, Any]]:
    """
    登記記録に関する事項（自由記述に近い）
    - 本店移転などの重要イベントを緩く抽出（必要に応じて辞書化・精緻化可能）
    """
    notes: List[Dict[str, Any]] = []
    body = "\n".join(sec.splitlines()[1:])

    # 文の区切りで緩く走査（。や改行で分割しても良い）
    for para in re.split(r"[。]\s*", body):
        if not para.strip():
            continue
        # 本店移転（from の抽出はヒューリスティック）
        if "本店移転" in para or "移転" in para:
            eff = wareki_to_date_str(para)  # 最初に見つかった和暦を効力発生日とみなす
            reg = None
            mreg = re.search(r"(令和|平成|昭和)\s*[\d０-９]+\s*年\s*[\d０-９]+\s*月\s*[\d０-９]+\s*日\s*登記", para)
            if mreg:
                reg = wareki_to_date_str(mreg.group(0))
            m_from = re.search(r"(\S+?)から本店移転", para)
            notes.append({
                "note": "本店移転",
                "from": m_from.group(1) if m_from else None,
                "effective_date": eff,
                "registration_date": reg
            })
        # ここに他のイベント（合併・解散・清算結了など）を追加拡張可能
    return notes


# =========================
# 7) 総合パース（この関数が最終JSONを返す）
# =========================
def parse_corporation_registry(pdf_path: Path) -> Dict[str, Any]:
    """
    総合パース：
    - PDFテキスト抽出→正規化
    - メタ抽出
    - セクション分割
    - 各セクションの専用パーサで構造化
    """
    raw = extract_text_from_pdf(pdf_path)
    norm = normalize_text(raw)

    meta = parse_metadata(norm)
    sections = split_sections(norm)

    profile: Dict[str, Any] = {}

    # 商号（company_nameは meta で拾えていなければ補完）
    if "商号" in sections:
        profile["trade_name"] = parse_trade_name(sections["商号"])
        if not meta.get("company_name"):
            meta["company_name"] = profile["trade_name"]["current"]

    # 本店（current + history）
    if "本店" in sections:
        profile["head_office"] = parse_head_office(sections["本店"])

    # 公告方法
    if "公告をする方法" in sections:
        profile["public_notice_method"] = parse_public_notice(sections["公告をする方法"])

    # 会社成立日（和暦→ISO）
    if "会社成立の年月日" in sections:
        profile["date_of_incorporation"] = parse_incorporation_date(sections["会社成立の年月日"])

    # 目的（箇条書き抽出）
    if "目的" in sections:
        profile["purposes"] = parse_purposes(sections["目的"])

    # 発行可能株式総数／発行済株式／資本金
    if "発行可能株式総数" in sections:
        profile["authorized_shares"] = parse_authorized_shares(sections["発行可能株式総数"])
    if "発行済株式の総数" in sections:
        profile["issued_shares"] = parse_issued_shares(sections["発行済株式の総数"])
    if "資本金の額" in sections:
        profile["capital"] = parse_capital(sections["資本金の額"])

    # 譲渡制限
    if "株式の譲渡制限に関する規定" in sections:
        profile["transfer_restrictions"] = parse_transfer_restrictions(sections["株式の譲渡制限に関する規定"])

    # 役員
    officers = []
    if "役員に関する事項" in sections:
        officers = parse_officers(sections["役員に関する事項"])

    # 登記記録
    reg_notes = []
    if "登記記録に関する事項" in sections:
        reg_notes = parse_registration_notes(sections["登記記録に関する事項"])

    return {
        "source": str(pdf_path),
        "metadata": meta,
        "company_profile": profile,
        "officers": officers,
        "registration_notes": reg_notes
    }


# =========================
# 8) CLI: ファイル入出力
# =========================
def main():
    ap = argparse.ArgumentParser(description="株式会社の登記簿（全部事項）PDF → JSON構造化（コメント厚め版）")
    ap.add_argument("pdf", type=str, help="入力PDFパス")
    ap.add_argument("-o", "--out", type=str, default="", help="出力JSONパス（省略時: 同名 .corp_registry.json）")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    assert pdf_path.exists(), f"PDF not found: {pdf_path}"

    data = parse_corporation_registry(pdf_path)

    out_path = Path(args.out) if args.out else pdf_path.with_suffix(".corp_registry.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()