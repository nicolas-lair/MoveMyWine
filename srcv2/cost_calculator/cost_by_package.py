from dataclasses import dataclass, field
from typing import Dict

from .constant import CostType
from .abstract_cost import AbstractCost
from .expedition import MultiRefExpedition


@dataclass(kw_only=True)
class ExtraPackageCost:
    extra_package_cost: float = 0  # No cost by default
    max_free_package: int = 0  # No cost by default
    multi_package_max_fee: float = 0  # No cost by default


class CostByPackageCalculator(AbstractCost):
    name: str = CostType.ByPackage
    costs_by_package: Dict[str, float] = field(default_factory=dict)
    extra_package_costs: ExtraPackageCost = field(default_factory=ExtraPackageCost)

    @property
    def base_cost_by_package(self) -> float:
        return sum(self.costs_by_package.values())

    def compute_extra_package_cost(self, n_package) -> float:
        cost = 0
        extra_packages = (n_package - self.extra_package_costs.max_free_package)
        if extra_packages > 0:
            cost = self.extra_package_costs.extra_package_cost * extra_packages
        cost = min(cost, self.extra_package_costs.multi_package_max_fee)
        return cost

    def _compute_cost(self, expedition: MultiRefExpedition, *args, **kwargs) -> float:
        n_packages = expedition.n_packages
        base_cost = n_packages * self.base_cost_by_package
        extra_cost = self.compute_extra_package_cost(n_packages)
        return base_cost + extra_cost
