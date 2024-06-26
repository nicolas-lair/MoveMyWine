from typing import Protocol, runtime_checkable, Callable

from .constant import CostType

PRECISION = 2

CostFunc = Callable[..., float]


def round_cost(digits: int = PRECISION) -> Callable[[CostFunc], CostFunc]:
    def decorator(func: CostFunc) -> CostFunc:
        def wrapper(*args, **kwargs):
            return round(func(*args, **kwargs), digits)

        return wrapper

    return decorator


@runtime_checkable
class BaseCostCalculator(Protocol):
    name: CostType
    compute_cost: Callable[..., float]
