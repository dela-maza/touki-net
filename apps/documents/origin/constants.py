# apps/documents/origin/constants.py
from enum import IntEnum

class CauseType(IntEnum):
    SALE = 1
    GIFT = 2
    DIVISION = 3

    @property
    def label(self):
        labels = {
            CauseType.SALE: "売買",
            CauseType.GIFT: "贈与",
            CauseType.DIVISION: "財産分与",
        }
        return labels.get(self, "不明")

    @classmethod
    def choices(cls):
        return [(c.value, c.label) for c in cls]

    @classmethod
    def from_id(cls, _id: int) -> "CauseType":
        try:
            return cls(_id)
        except ValueError:
            return cls.SALE