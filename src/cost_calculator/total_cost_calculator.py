from dataclasses import dataclass

from src.cost_calculator.cost_collection import (
    BaseCostList,
    ModCostCollection,
    DetailedCost,
)
from src.cost_calculator.constant import CostType


@dataclass
class TotalCostCalculator:
    cost_collection: BaseCostList
    cost_modulator: ModCostCollection
    name: CostType = CostType.Total

    def compute_cost(self, agg: bool = True, **kwargs) -> float | DetailedCost:
        cost_by_type = self.cost_collection.compute_cost(**kwargs)
        cost_by_type = self.cost_modulator.compute_cost(
            cost_by_type=cost_by_type, **kwargs
        )
        if agg:
            total_cost = sum(cost_by_type.values(), 0)
            total_cost = round(total_cost, 2)
            return total_cost
        else:
            return cost_by_type
