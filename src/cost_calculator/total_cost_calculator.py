from dataclasses import dataclass
from src.cost_calculator.cost_collection import CostCollectionCalculator
from src.cost_calculator.constant import CostType
from src.cost_calculator.cost_modulator import ModulatedCostCollection


@dataclass
class TotalCostCalculator:
    cost_collection: CostCollectionCalculator
    cost_modulator: dict[CostType, ModulatedCostCollection]
    name: CostType = CostType.Total

    def compute_cost(self, agg: bool = True, **kwargs) -> float | dict[CostType, float]:
        cost_by_type = self.cost_collection.compute_cost(**kwargs)
        for mod_name, mod in self.cost_modulator.items():
            cost_by_type[mod_name] = mod.compute_cost(
                cost_by_type=cost_by_type, **kwargs
            )
        if agg:
            total_cost = sum(cost_by_type.values(), 0)
            total_cost = round(total_cost, 2)
            return total_cost
        else:
            return cost_by_type
