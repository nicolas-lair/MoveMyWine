from src.constant import N_EXPEDITION
from .base_cost import BaseCost
from .constant import CostType


class MonthlyCostCalculator(BaseCost):
    def __init__(self, name: str = CostType.Monthly, **kwargs):
        self.name = name
        self.cost = kwargs

    def compute_cost(
        self, n_expedition_by_month: int = N_EXPEDITION, **kwargs
    ) -> float:
        total_cost = sum(self.cost.values()) / n_expedition_by_month
        return total_cost
