from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

from .expedition import MultiRefExpedition


class AbstractCost(ABC):
    def __init__(self, gas_modulated: Optional[bool] = False):
        self.gas_modulated: bool = gas_modulated
        self.compute_cost = self.apply_gas_modulation_factory(self._compute_cost)

    @abstractmethod
    def _compute_cost(self, expedition: MultiRefExpedition, *args, **kwargs) -> float:
        """ Compute cost for a given number of bottles"""
        ...

    def apply_gas_modulation_factory(self, func):
        def gas_modulated_cost(gas_factor, *args, **kwargs):
            cost = func(*args, **kwargs)
            if self.gas_modulated:
                cost *= gas_factor
            return cost
        return gas_modulated_cost
