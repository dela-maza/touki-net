# apps/amount_document/calculator.py
from typing import List, Dict, Final, Union, Iterable


class AmountDocumentCalculator:
    def __init__(
            self,
            reward_amounts: list[int],   # 報酬
            expense_amounts: list[int],  # 経費
            apply_consumption_tax: bool,
            apply_withholding: bool,
    ) -> None:
        from flask import current_app
        tax = current_app.config["TAX_RATE"]

        self.consumption_tax_rate: float = tax["consumption_tax"]
        self.withholding_exemption_amount: int = tax["withholding_exemption"]
        self.withholding_tax_rate: float = tax["withholding_tax"]

        # None を 0 に変換したいならここで吸収
        self.reward_amounts = [x or 0 for x in reward_amounts]
        self.expense_amounts = [x or 0 for x in expense_amounts]

        self.apply_consumption_tax = apply_consumption_tax
        self.apply_withholding = apply_withholding

    def total_reward_amount(self) -> int:
        return sum(self.reward_amounts)

    def total_expense_amount(self) -> int:
        return sum(self.expense_amounts)

    def consumption_tax_amount(self) -> int:
        return int(self.total_reward_amount() * self.consumption_tax_rate) if self.apply_consumption_tax else 0

    def withholding_tax_amount(self) -> int:
        if not self.apply_withholding:
            return 0
        taxable: Final[int] = max(0, self.total_reward_amount() - self.withholding_exemption_amount)
        return int(taxable * self.withholding_tax_rate)

    def calculate_totals(self, round_to_hundred: bool = False, *, round_unit: int | None = None) -> Dict[str, int]:
        """
        round_to_hundred=True か round_unit=100 のどちらでも100円未満切り捨て。
        将来 10円単位などにしたい時は round_unit に任意の整数を渡せる。
        """
        reward: Final[int] = self.total_reward_amount()
        expense: Final[int] = self.total_expense_amount()
        tax: Final[int] = self.consumption_tax_amount()
        withholding: Final[int] = self.withholding_tax_amount()
        subtotal: Final[int] = reward + expense

        grand_total = subtotal + tax - withholding

        unit = 100 if (round_to_hundred and round_unit is None) else round_unit
        if unit and unit > 1:
            grand_total = (grand_total // unit) * unit  # 切り捨て

        return {
            "subtotal": subtotal,
            "reward": reward,
            "expense": expense,
            "tax": tax,
            "withholding": withholding,
            "grand_total": grand_total,
        }