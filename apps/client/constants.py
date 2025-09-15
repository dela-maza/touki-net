# apps/client/constants.py
from enum import Enum

class ClientType(Enum):
    """クライアント種別 (DB保存用: int)"""
    RIGHT_HOLDER = 1
    OBLIGATION_HOLDER = 2
    APPLICANT = 3

    @property
    def label(self) -> str:
        labels = {
            ClientType.RIGHT_HOLDER: "権利者",
            ClientType.OBLIGATION_HOLDER: "義務者",
            ClientType.APPLICANT: "申請人",
        }
        return labels.get(self, "不明")

    @classmethod
    def from_id(cls, _id: int) -> "ClientType":
        try:
            return cls(_id)
        except ValueError:
            return cls.RIGHT_HOLDER