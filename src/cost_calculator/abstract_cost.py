from abc import ABC, abstractmethod
from typing import Optional


class AbstractCost(ABC):
    def __init__(self, gas_modulated: Optional[bool] = False):
        self.gas_modulated: bool = gas_modulated
        # self.compute_cost = self.apply_gas_modulation_factory(self._compute_cost)

    @abstractmethod
    def _compute_cost(self, *args, **kwargs) -> float:
        """Compute cost for a given number of bottles"""
        ...

    def compute_cost(self, gas_factor: Optional[float] = None, *args, **kwargs):
        cost = self._compute_cost(*args, **kwargs)
        if self.gas_modulated:
            assert 1 <= gas_factor <= 2, "Gas factor should be between 1 and 2."
            cost *= gas_factor
        return cost
