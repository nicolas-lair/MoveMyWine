from collections import UserDict

from .constant import CostType
from .abstract_cost import AbstractCost
from .expedition import MultiRefExpedition


class TotalCostCalculator(UserDict[CostType, AbstractCost]):
    def compute_cost(self, gas_factor: float, expedition: MultiRefExpedition, *args, **kwargs):
        detailed_cost = {
            k: cc.compute_cost(expedition=expedition,  *args, gas_factor=gas_factor, **kwargs)
            for k, cc in self.items()
        }
        print(detailed_cost)
        total_cost = sum(detailed_cost.values(), 0)
        return total_cost
