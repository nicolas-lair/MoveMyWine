from typing import Optional

import pandas as pd
from .abstract_cost import AbstractCost
from .constant import CostType


class FixedCostByExpe(AbstractCost):
    def __init__(self, gas_modulated: Optional[bool] = False, name: Optional[str] = CostType.Expedition, **kwargs):
        super().__init__(gas_modulated=gas_modulated)
        self.fixed_cost_by_expedition = kwargs
        self.name = name

    def _compute_cost(self, *args, **kwargs):
        return sum(self.fixed_cost_by_expedition.values())
