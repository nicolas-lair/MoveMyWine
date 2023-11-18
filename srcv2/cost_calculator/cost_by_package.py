from dataclasses import dataclass
from typing import Optional

from .constant import CostType
from .abstract_cost import AbstractCost
from .expedition import MultiRefExpedition


@dataclass(kw_only=True)
class ExtraPackageCost:
    extra_package_cost: float = 0  # No cost by default
    max_free_package: int = 0  # No cost by default
    multi_package_max_fee: float = 0  # No cost by default

    def compute_extra_cost(self, n_packages: int) -> float:
        extra_package = max(0, n_packages - self.max_free_package)
        extra_cost = min(
            self.multi_package_max_fee, self.extra_package_cost * extra_package
        )
        return extra_cost


class CostByPackageCalculator(AbstractCost):
    def __init__(
        self,
        gas_modulated: bool,
        extra_package_costs: ExtraPackageCost,
        costs_by_package: Optional[dict[str, float]] = None,
        name: str = CostType.ByPackage,
    ):
        super().__init__(gas_modulated=gas_modulated)
        if costs_by_package is None:
            costs_by_package = {}
        self.name: str = name
        self.costs_by_package: dict[str, float] = costs_by_package
        self.extra_package_costs: ExtraPackageCost = extra_package_costs

    @property
    def base_cost_by_package(self) -> float:
        return sum(self.costs_by_package.values())

    def _compute_cost(self, expedition: MultiRefExpedition, *args, **kwargs) -> float:
        n_packages = expedition.n_packages
        base_cost = n_packages * self.base_cost_by_package
        extra_cost = self.extra_package_costs.compute_extra_cost(n_packages)
        return base_cost + extra_cost
