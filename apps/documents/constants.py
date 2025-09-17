from enum import Enum


class DocumentType(str, Enum):
    """統合ドキュメントの種類"""
    AMOUNT = "amount"  # 金額帳票
    REQUIRED = "required"  # 必要書類
    DELIVERY = "delivery"  # 納品書
    RECEIPT = "receipt"  # 預かり証
    PROXY = "proxy"  # 委任状
    ORIGIN = "origin"  # 登記原因証明情報

    def __str__(self) -> str:
        return self.value
