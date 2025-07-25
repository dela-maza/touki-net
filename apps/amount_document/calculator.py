### amount_document/calculator.py
from typing import List, Dict

class AmountDocumentCalculator:
    CONSUMPTION_TAX_RATE: float = 0.10
    WITHHOLDING_EXEMPTION_AMOUNT: int = 10000
    WITHHOLDING_TAX_RATE: float = 0.1021

    def __init__(
        self,
        reward_amounts: List[int],
        expense_amounts: List[int],
        apply_consumption_tax: bool,
        apply_withholding: bool,
    ) -> None:
        self.reward_amounts: List[int] = reward_amounts
        self.expense_amounts: List[int] = expense_amounts
        self.apply_consumption_tax: bool = apply_consumption_tax
        self.apply_withholding: bool = apply_withholding

    def total_reward_amount(self) -> int:
        return sum(self.reward_amounts)

    def total_expense_amount(self) -> int:
        return sum(self.expense_amounts)

    def consumption_tax_amount(self) -> int:
        if self.apply_consumption_tax:
            return int(self.total_reward_amount() * self.CONSUMPTION_TAX_RATE)
        return 0

    def withholding_tax_amount(self) -> int:
        if self.apply_withholding:
            taxable: int = max(0, self.total_reward_amount() - self.WITHHOLDING_EXEMPTION_AMOUNT)
            return int(taxable * self.WITHHOLDING_TAX_RATE)
        return 0

    def calculate_totals(self) -> Dict[str, int]:
        reward: int = self.total_reward_amount()
        expense: int = self.total_expense_amount()
        tax: int = self.consumption_tax_amount()
        withholding: int = self.withholding_tax_amount()
        grand_total: int = reward + tax + expense - withholding
        return {
            'reward': reward,
            'expense': expense,
            'tax': tax,
            'withholding': withholding,
            'grand_total': grand_total
        }