import pandas as pd
from .abstract_cost import AbstractCost
from .constant import CostType


class FixedCostByExpe(AbstractCost):
    def __init__(self, **kwargs):
        super().__init__()
        self.fixed_cost_by_expedition = kwargs

    @property
    def total_cost(self) -> float:
        total_cost = sum(self.fixed_cost_by_expedition.values())
        return total_cost

    def compute_cost(self, *args, **kwargs):
        return self.total_cost

    def compute_cost_by_bottle(self, *args, **kwargs):
        N = 100
        cost_by_bottle = pd.DataFrame(index=range(1, N), data=self.compute_cost(), columns=[CostType.Expedition])
        return cost_by_bottle
