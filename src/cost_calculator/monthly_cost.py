from typing import Optional

from src.constant import N_EXPEDITION
from .abstract_cost import AbstractCost
from .constant import CostType


class MonthlyCostCalculator(AbstractCost):
    def __init__(
        self,
        gas_modulated: Optional[bool] = False,
        name: Optional[str] = CostType.Monthly,
        **kwargs,
    ):
        super().__init__(gas_modulated=gas_modulated)
        self.monthly_cost = kwargs
        self.name = name

    def _compute_cost(
        self, n_expedition_by_month: int = N_EXPEDITION, *args, **kwargs
    ) -> float:
        total_cost = sum(self.monthly_cost.values()) / n_expedition_by_month
        return total_cost
