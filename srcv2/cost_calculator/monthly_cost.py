import pandas as pd
from src.constant import N_EXPEDITION
from .abstract_cost import AbstractCost
from .constant import CostType


class MonthlyCostCalculator(AbstractCost):
    def __init__(self, **kwargs):
        super().__init__()
        self.monthly_cost = kwargs

    def compute_cost(self, n_expedition_by_month: int = N_EXPEDITION, *args, **kwargs) -> float:
        total_cost = sum(self.monthly_cost.values()) / n_expedition_by_month
        return total_cost

    def compute_cost_by_bottle(self, n_expedition_by_month: int = N_EXPEDITION, *args, **kwargs):
        N = 100
        cost_by_bottle = pd.DataFrame(
            index=range(1, N),
            data=self.compute_cost(n_expedition_by_month=n_expedition_by_month, *args, **kwargs),
            columns=[CostType.Monthly]
        )
        return cost_by_bottle
