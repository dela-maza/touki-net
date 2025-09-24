# apps/commerce/services/commerce/services.py
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from apps.shared.wareki import wareki_str_to_iso  # 保存は ISO に統一
from apps.shared.jp_amount import jp_amount_to_int
from apps.register.shared.pdf_reader import extract_text_from_pdf
from apps.register.commerce.pdf.services.normalize import normalize_text, ZEN2HAN

# =========================
# 4) メタ情報：as_of・法人番号・会社名など
# =========================
def parse_metadata(norm: str) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}

    m = re.search(r"(\d{4})[／/](\d{2})[／/](\d{2})\s+(\d{2})：?(\d{2}).*現在の情報です", norm)
    if m:
        meta["as_of"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}"

    m = re.search(r"会社法人等番号\s*([0-9０-９\-－]+)", norm)
    if m:
        meta["corporate_number"] = m.group(1).translate(ZEN2HAN)

    m = re.search(r"\n商\s*号\s*(.+?)(?:\n|$)", norm)
    if m:
        meta["company_name"] = re.sub(r"\s+", " ", m.group(1)).strip()
    return meta

# =========================
# 5) セクション分割
# =========================
SECTION_KEYS = [
    "商号", "本店", "公告をする方法", "会社成立の年月日", "目的",
    "発行可能株式総数", "発行済株式の総数", "資本金の額",
    "株式の譲渡制限に関する規定", "役員に関する事項", "登記記録に関する事項"
]

def split_sections(norm: str) -> Dict[str, str]:
    positions = []
    for key in SECTION_KEYS:
        for m in re.finditer(rf"\n{re.escape(key)}\s", norm):
            positions.append((m.start(), key))
    positions.sort()

    sections: Dict[str, str] = {}
    for i, (pos, key) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(norm)
        sections[key] = norm[pos:end]
    return sections

# =========================
# 6) 各セクションパーサ
# =========================
def parse_trade_name(sec: str) -> Dict[str, Any]:
    line = " ".join(sec.splitlines()[0:2])
    m = re.search(r"商\s*号\s*(.+)$", line)
    current = m.group(1).strip() if m else ""
    return {"current": current, "history": []}

def parse_public_notice(sec: str) -> str:
    m = re.search(r"公告をする方法\s*(.+)", sec)
    return m.group(1).strip() if m else ""

def parse_incorporation_date(sec: str) -> Optional[str]:
    m = re.search(r"会社成立の年月日\s*([^\n]+)", sec)
    return wareki_str_to_iso(m.group(1)) if m else None

def parse_purposes(sec: str) -> Dict[str, Any]:
    body = "\n".join(sec.splitlines()[1:]).strip()
    items: List[str] = []
    for ln in body.splitlines():
        if re.search(r"^\d+[．\.、]?\s", ln) or re.search(r"^①|^②|^③|^④|^⑤|^⑥|^⑦|^⑧|^⑨|^⑩", ln):
            items.append(re.sub(r"\s+", " ", ln).strip())
        elif items and (ln.startswith("　") or ln.startswith(" ") * 2):
            items[-1] = items[-1] + " " + re.sub(r"\s+", " ", ln).strip()
    return {"items": items}

def parse_authorized_shares(sec: str) -> Dict[str, Any]:
    m = re.search(r"発行可能株式総数\s*([^\n]+)", sec)
    raw = m.group(1).strip() if m else ""
    val = jp_amount_to_int(raw)
    return {"raw": raw, "value": val}

def parse_issued_shares(sec: str) -> Dict[str, Any]:
    m = re.search(r"発行済株式の総数[^\n]*\n?\s*([^\n]+)", sec)
    raw = (m.group(1).strip() if m else "").replace("並びに種類及び数", "").strip()
    val = jp_amount_to_int(raw)
    return {"raw": raw, "value": val}

def parse_capital(sec: str) -> Dict[str, Any]:
    m = re.search(r"資本金の額\s*([^\n]+)", sec)
    raw = m.group(1).strip() if m else ""
    val = jp_amount_to_int(raw)
    return {"raw": raw, "value_jpy": val}

def parse_transfer_restrictions(sec: str) -> str:
    m = re.search(r"株式の譲渡制限に関する規定\s*(.+)", sec)
    return m.group(1).strip() if m else ""

def parse_head_office(sec: str) -> Dict[str, Any]:
    lines = [ln for ln in sec.splitlines() if ln.strip()]
    moves: List[Dict[str, Any]] = []
    pending_addr = None

    for ln in lines[1:]:
        if re.search(r"(都|道|府|県).+(市|区|郡|町|村)", ln) and not re.search(r"(就任|辞任|更正|登記|移転)", ln):
            pending_addr = re.sub(r"\s+", " ", ln).strip()
            continue

        if "移転" in ln or "登記" in ln:
            eff = wareki_str_to_iso(ln) if "移転" in ln else None
            reg = wareki_str_to_iso(ln) if "登記" in ln else None
            if pending_addr:
                rec = next((x for x in moves if x.get("new") == pending_addr), None)
                if not rec:
                    rec = {"new": pending_addr, "effective_date": None, "registration_date": None, "event": "移転"}
                    moves.append(rec)
                if eff:
                    rec["effective_date"] = eff
                if reg:
                    rec["registration_date"] = reg

    def sort_key(x):
        return (x.get("effective_date") or x.get("registration_date") or "9999-99-99")

    moves_sorted = sorted(moves, key=sort_key)

    history: List[Dict[str, Any]] = []
    for i in range(1, len(moves_sorted)):
        old = moves_sorted[i - 1].get("new")
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
    lines = [ln for ln in sec.splitlines() if ln.strip()]
    officers: List[Dict[str, Any]] = []
    current_officer: Optional[Dict[str, Any]] = None
    last_address: Optional[str] = None

    ROLE_PAT = r"(代表取締役|取締役|監査役|会計参与|清算人)"
    for ln in lines[1:]:
        if re.search(r"(都|道|府|県).+(市|区|郡|町|村).*(番|号|丁目|F|階)", ln) and not re.search(ROLE_PAT, ln):
            last_address = re.sub(r"\s+", " ", ln).strip()
            continue

        m = re.search(rf"{ROLE_PAT}\s+(.+)", ln)
        if m:
            if current_officer:
                officers.append(current_officer)
            role = m.group(1)
            name = re.sub(r"\s+", " ", m.group(2)).strip()
            current_officer = {"role": role, "name": name, "address": last_address, "events": []}
            last_address = None
            continue

        if re.search(r"(就任|退任|辞任|更正|住所移転|登記)", ln):
            date = wareki_str_to_iso(ln)
            event = next((k for k in ["就任", "退任", "辞任", "更正", "住所移転", "登記"] if k in ln), None)
            if current_officer and event and date:
                current_officer["events"].append({"event": event, "date": date})
            continue

    if current_officer:
        officers.append(current_officer)
    return officers

def parse_registration_notes(sec: str) -> List[Dict[str, Any]]:
    notes: List[Dict[str, Any]] = []
    body = "\n".join(sec.splitlines()[1:])

    for para in re.split(r"[。]\s*", body):
        if not para.strip():
            continue
        if "本店移転" in para or "移転" in para:
            eff = wareki_str_to_iso(para)
            reg = None
            mreg = re.search(r"(令和|平成|昭和|大正|明治)\s*[\d０-９]+\s*年\s*[\d０-９]+\s*月\s*[\d０-９]+\s*日\s*登記", para)
            if mreg:
                reg = wareki_str_to_iso(mreg.group(0))
            m_from = re.search(r"(\S+?)から本店移転", para)
            notes.append({
                "note": "本店移転",
                "from": m_from.group(1) if m_from else None,
                "effective_date": eff,
                "registration_date": reg
            })
    return notes

# =========================
# 7) 総合パース
# =========================
def parse_corporation_registry(pdf_path: Path) -> Dict[str, Any]:
    raw = extract_text_from_pdf(pdf_path)
    norm = normalize_text(raw)

    meta = parse_metadata(norm)
    sections = split_sections(norm)

    profile: Dict[str, Any] = {}

    if "商号" in sections:
        profile["trade_name"] = parse_trade_name(sections["商号"])
        if not meta.get("company_name"):
            meta["company_name"] = profile["trade_name"]["current"]

    if "本店" in sections:
        profile["head_office"] = parse_head_office(sections["本店"])

    if "公告をする方法" in sections:
        profile["public_notice_method"] = parse_public_notice(sections["公告をする方法"])

    if "会社成立の年月日" in sections:
        profile["date_of_incorporation"] = parse_incorporation_date(sections["会社成立の年月日"])

    if "目的" in sections:
        profile["purposes"] = parse_purposes(sections["目的"])

    if "発行可能株式総数" in sections:
        profile["authorized_shares"] = parse_authorized_shares(sections["発行可能株式総数"])
    if "発行済株式の総数" in sections:
        profile["issued_shares"] = parse_issued_shares(sections["発行済株式の総数"])
    if "資本金の額" in sections:
        profile["capital"] = parse_capital(sections["資本金の額"])

    if "株式の譲渡制限に関する規定" in sections:
        profile["transfer_restrictions"] = parse_transfer_restrictions(sections["株式の譲渡制限に関する規定"])

    officers = []
    if "役員に関する事項" in sections:
        officers = parse_officers(sections["役員に関する事項"])

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