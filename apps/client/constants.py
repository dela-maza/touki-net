# apps/client/constants.py
from enum import Enum


class EntityType(Enum):
    INDIVIDUAL = 1
    CORPORATION = 2

    @property
    def label(self) -> str:
        return {
            EntityType.INDIVIDUAL: "個人",
            EntityType.CORPORATION: "法人",
        }.get(self, "不明")

    @property
    def honorific(self) -> str:
        return {
            EntityType.INDIVIDUAL: "様",
            EntityType.CORPORATION: "御中",
        }.get(self, "")

class ClientType(Enum):
    """クライアント種別 (登記上の立場)"""
    RIGHT_HOLDER = 1      # 権利者
    OBLIGATION_HOLDER = 2 # 義務者
    APPLICANT = 3         # 申請人

    @property
    def label(self) -> str:
        return {
            ClientType.RIGHT_HOLDER: "権利者",
            ClientType.OBLIGATION_HOLDER: "義務者",
            ClientType.APPLICANT: "申請人",
        }.get(self, "不明")

    @classmethod
    def from_id(cls, _id: int) -> "ClientType":
        try:
            return cls(_id)
        except ValueError:
            return cls.RIGHT_HOLDER  # デフォルト
