### amount_document/calculator.py
from typing import List, Dict, Final,Union
from apps.amount_document.config_loader import load_config

class AmountDocumentCalculator:
    def __init__(
            self,
            reward_amounts: List[int],
            expense_amounts: List[int],
            apply_consumption_tax: bool,
            apply_withholding: bool,
    ) -> None:
        tax_config = AmountDocumentCalculator.get_tax_config()
        self.consumption_tax_rate: Final[float] = tax_config["consumption_tax"] # 消費税率
        self.withholding_exemption_amount: Final[int] = tax_config["withholding_exemption"] # 源泉徴収控除額
        self.withholding_tax_rate: Final[float] = tax_config["withholding_tax"] # 源泉徴収額

        self.reward_amounts: Final[List[int]] = reward_amounts
        self.expense_amounts: Final[List[int]] = expense_amounts
        self.apply_consumption_tax: Final[bool] = apply_consumption_tax
        self.apply_withholding: Final[bool] = apply_withholding

    def total_reward_amount(self) -> int:
        return sum(self.reward_amounts)

    def total_expense_amount(self) -> int:
        return sum(self.expense_amounts)

    def consumption_tax_amount(self) -> int:
        if self.apply_consumption_tax:
            return int(self.total_reward_amount() * self.consumption_tax_rate)
        return 0

    def withholding_tax_amount(self) -> int:
        if self.apply_withholding:
            taxable: Final[int] = max(0, self.total_reward_amount() - self.withholding_exemption_amount)
            return int(taxable * self.withholding_tax_rate)
        return 0

    def calculate_totals(self) -> Dict[str, int]:
        reward: Final[int] = self.total_reward_amount()
        expense: Final[int] = self.total_expense_amount()
        tax: Final[int] = self.consumption_tax_amount()
        withholding: Final[int] = self.withholding_tax_amount()
        grand_total: Final[int] = reward + tax + expense - withholding
        return {
            "reward": reward,
            "expense": expense,
            "tax": tax,
            "withholding": withholding,
            "grand_total": grand_total,
        }

    @staticmethod
    def get_tax_config() -> Dict[str, Union[int, float]]:
        """TAX_RATE設定を返す"""
        return load_config()["TAX_RATE"]

    def get_display_totals(self) -> Dict[str, int]:
        """
        テンプレートで使いやすい計算済みの金額をまとめて取得
        ＊消費税と源泉徴収額はフラグによって0になる可能性あり
        """
        reward = self.total_reward_amount()
        expense = self.total_expense_amount()
        tax = self.consumption_tax_amount() if self.apply_consumption_tax else 0
        withholding = self.withholding_tax_amount() if self.apply_withholding else 0
        subtotal = reward + expense
        total = subtotal + tax - withholding

        return {
            "subtotal": subtotal,              # 小計（報酬＋実費）
            "reward": reward,                  # 報酬合計
            "expense": expense,                # 実費合計
            "tax": tax,                        # 消費税額（フラグ有効時のみ）
            "withholding": withholding,        # 源泉徴収額（フラグ有効時のみ）
            "grand_total": total,              # 差引請求額（合計）
        }