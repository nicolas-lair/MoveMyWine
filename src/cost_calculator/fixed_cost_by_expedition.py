from .base_cost import BaseCostCalculator, round_cost
from .constant import CostType


class FixedCostByExpe(BaseCostCalculator):
    def __init__(self, name: str = CostType.Expedition, **kwargs: float):
        self.name = name
        self.cost = kwargs

    @round_cost()
    def compute_cost(self, **kwargs) -> float:
        return sum(self.cost.values())
