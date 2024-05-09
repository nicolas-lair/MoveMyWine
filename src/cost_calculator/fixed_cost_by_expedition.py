from .base_cost import BaseCost
from .constant import CostType


class FixedCostByExpe(BaseCost):
    def __init__(self, name: str = CostType.Expedition, **kwargs: float):
        self.name = name
        self.cost = kwargs

    def compute_cost(self, **kwargs) -> float:
        return sum(self.cost.values())
