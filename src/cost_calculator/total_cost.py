import dataclasses
import functools
from typing import Dict

import pandas as pd

from .constant import CostType
from .abstract_cost import AbstractCost


def _apply_gas_factor(func):
    @functools.wraps
    def wrapper(self, gas_factor: float, *args, **kwargs):
        print(args)
        print(kwargs)
        cost = func(self, *args, **kwargs)
        if self.gas_modulation_applicability:
            cost *= gas_factor
        return cost

    return wrapper


@dataclasses.dataclass
class GasModulatedCost(AbstractCost):
    cost_calculator: AbstractCost
    gas_modulation_applicability: bool

    # @_apply_gas_factor
    def compute_cost_by_bottle(self, gas_factor: float, *args, **kwargs):
        cost = self.cost_calculator.compute_cost_by_bottle(*args, **kwargs)
        if self.gas_modulation_applicability:
            cost *= gas_factor
        return cost
        # return self.cost_calculator.compute_cost_by_bottle(*args, **kwargs)

    # @_apply_gas_factor
    def compute_cost(self, gas_factor: float, *args, **kwargs):
        cost = self.cost_calculator.compute_cost(*args, **kwargs)
        if self.gas_modulation_applicability:
            cost *= gas_factor
        return cost
        # return self.cost_calculator.compute_cost(*args, **kwargs)


class TotalCostCalculator(AbstractCost):
    costs: Dict[CostType, GasModulatedCost]

    def compute_cost(self, gas_factor: float, *args, **kwargs):
        total_cost = sum(
            [cc.compute_cost(gas_factor, *args, **kwargs) for cc in self.costs.values()])
        return total_cost

    def compute_cost_by_bottle(self, gas_factor: float, *args, **kwargs):
        total_cost = pd.concat(
            [cc.compute_cost_by_bottle(gas_factor, *args, **kwargs) for cc in self.costs.values()], axis=1
        )
        total_cost = total_cost.sum(axis=1).rename(CostType.Total)
        return total_cost
