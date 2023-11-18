from collections import UserDict
from typing import Union

from .constant import CostType
from .abstract_cost import AbstractCost
from .expedition import MultiRefExpedition, SingleRefExpedition


class TotalCostCalculator(UserDict[CostType, AbstractCost]):
    def compute_cost(
        self,
        gas_factor: float,
        expedition: Union[SingleRefExpedition, MultiRefExpedition],
        return_details: bool = False,
        *args,
        **kwargs,
    ):
        detailed_cost = {
            k: cc.compute_cost(
                expedition=expedition, *args, gas_factor=gas_factor, **kwargs
            )
            for k, cc in self.items()
        }
        if return_details:
            return detailed_cost
        total_cost = sum(detailed_cost.values(), 0)
        return total_cost
