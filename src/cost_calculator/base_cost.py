from typing import Protocol, runtime_checkable, Callable


@runtime_checkable
class BaseCostCalculator(Protocol):
    name: str
    compute_cost: Callable[..., float]
