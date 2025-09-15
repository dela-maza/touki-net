# apps/amount/constants.py

MIN_ENTRIES = 20
from enum import Enum
from apps.client.constants import ClientType

class AmountDocumentType(Enum):
    ESTIMATE = ("見積",  "ESTIMATE")
    INVOICE  = ("請求",  "INVOICE")
    RECEIPT  = ("領収",  "RECEIPT")

    def __init__(self, label_ja: str, note_key: str):
        self._label = label_ja
        self._note_key = note_key

    @property
    def label(self) -> str:
        """UI 表示用のラベル"""
        return self._label

    @property
    def note_key(self) -> str:
        """NOTE_DEFAULTS のキー名"""
        return self._note_key

    @classmethod
    def get_labels(cls) -> dict[str, str]:
        """テンプレートやビューで一括利用するラベル辞書"""
        return {member.name.lower(): member.label for member in cls}


# ClientType -> config.ini セクション名の対応
DEFAULT_ENTRY_SECTION_MAP: dict[ClientType, str] = {
    ClientType.RIGHT_HOLDER:      "DEFAULT_ENTRIES_RIGHT_HOLDER",
    ClientType.OBLIGATION_HOLDER: "DEFAULT_ENTRIES_OBLIGATION_HOLDER",
    ClientType.APPLICANT:         "DEFAULT_ENTRIES_APPLICANT",
}
