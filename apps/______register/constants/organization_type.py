# apps/______register/constants/organization_type.py
from enum import Enum

class OrganizationType(Enum):
    KK = "KK"         # 株式会社 (Kabushiki Kaisha)
    YK = "YK"         # 有限会社 (Yugen Kaisha)
    GK = "GK"         # 合同会社 (Godo Kaisha)
    SHADAN = "SHADAN" # 一般社団法人

    # --- ラベル辞書 ---
    _JP_LABELS = {
        "KK": "株式会社",
        "YK": "有限会社",
        "GK": "合同会社",
        "SHADAN": "一般社団法人",
    }

    _EN_LABELS = {
        "KK": "Joint-Stock Company",
        "YK": "Limited Company (Yugen)",
        "GK": "LLC (Godo Company)",
        "SHADAN": "General Incorporated Association",
    }

    # --- インスタンスメソッド ---
    @property
    def label_ja(self) -> str:
        return self._JP_LABELS[self.value]

    @property
    def label_en(self) -> str:
        return self._EN_LABELS[self.value]

    def to_labels(self) -> dict:
        """辞書形式でラベル群を返す"""
        return {"code": self.value, "ja": self.label_ja, "en": self.label_en}

    # --- クラスメソッド ---
    @classmethod
    def from_text(cls, text: str) -> "OrganizationType | None":
        """OCR等で抽出した日本語から推定"""
        t = (text or "").strip()
        if "株式会社" in t:
            return cls.KK
        if "有限会社" in t:
            return cls.YK
        if "合同会社" in t:
            return cls.GK
        if "一般社団法人" in t or "一般 社団 法人" in t:
            return cls.SHADAN
        return None