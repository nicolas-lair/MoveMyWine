from collections import UserList
from typing import Union

from .constant import CostType
from .base_cost import BaseCostCalculator
from .expedition import MultiRefExpedition, SingleRefExpedition
from .cost_modulator import ModulatedCostCalculator

DetailedCost = dict[CostType, float]


class BaseCostList(UserList[BaseCostCalculator]):
    def compute_cost(
        self,
        expedition: Union[SingleRefExpedition, MultiRefExpedition],
        **kwargs,
    ) -> DetailedCost:
        if expedition.n_bottles == 0:
            detailed_cost = {cost_.name: 0.0 for cost_ in self}
        else:
            detailed_cost = {
                cost_.name: cost_.compute_cost(expedition=expedition, **kwargs)
                for cost_ in self
            }
        return detailed_cost


class ModCostCollection(UserList[ModulatedCostCalculator]):
    def compute_cost(self, cost_by_type: DetailedCost, **kwargs) -> DetailedCost:
        detailed_cost = cost_by_type | {
            mod.name: mod.compute_cost(cost_by_type=cost_by_type, **kwargs)
            for mod in self
        }
        return detailed_cost
