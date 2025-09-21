# apps/register/parser/commerce/commerce_parser.py
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class ParseResult:
    data: Dict[str, Any]
    errors: List[Dict[str, Any]]
    confidence: Dict[str, float]
    raw_text: str

class CommerceRegisterParser:
    def __init__(self, text: str, *, file_name: str | None = None):
        self.text = text
        self.file_name = file_name
        self.errors: List[Dict[str, Any]] = []
        self.confidence: Dict[str, float] = {}

    @classmethod
    def from_pdf(cls, pdf_bytes: bytes, file_name: str | None = None) -> "CommerceRegisterParser":
        # base.extract_text(pdf_bytes) などを利用
        text = extract_text_from_pdf(pdf_bytes)   # 実装は base.py に
        return cls(text, file_name=file_name)

    def parse(self) -> ParseResult:
        t = normalize_text(self.text)
        blocks = split_blocks(t)  # 本店/目的/公告/資本金/株式/役員/履歴 等の塊に分割

        company = parse_company_block(blocks)
        officers = parse_officers_block(blocks)
        events = parse_events_block(blocks)

        data = {
            "source": build_source_meta(self.file_name, t),
            "company": company,
            "officers": officers,
            "articles": derive_articles_from(events),
            "registration_events": events,
            "confidence": self.confidence,
            "errors": self.errors,
            "normalized": {
                "dates": "yyyy-mm-dd",
                "numbers": "narrow",
            },
        }
        return ParseResult(data=data, errors=self.errors, confidence=self.confidence, raw_text=t)