from typing import Protocol, runtime_checkable, Callable


@runtime_checkable
class BaseCost(Protocol):
    name: str
    compute_cost: Callable[..., float]

    # def compute_cost(self, gas_factor: Optional[float] = None, *args, **kwargs):
    #     cost = self._compute_cost(*args, **kwargs)
    #     if self.gas_modulated:
    #         assert 1 <= gas_factor <= 2, "Gas factor should be between 1 and 2."
    #         cost *= gas_factor
    #     return cost
