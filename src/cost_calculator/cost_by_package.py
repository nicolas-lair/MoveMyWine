from collections import defaultdict
from dataclasses import dataclass, field

from .constant import CostType
from .base_cost import BaseCost
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


@dataclass
class CostByPackageCalculator(BaseCost):
    extra_package_costs: ExtraPackageCost
    costs_by_package: dict[str, float] = field(default_factory=lambda: defaultdict())
    name: str = CostType.ByPackage

    @property
    def base_cost_by_package(self) -> float:
        return sum(self.costs_by_package.values())

    def compute_cost(self, expedition: MultiRefExpedition, **kwargs) -> float:
        n_packages = expedition.n_packages
        base_cost = n_packages * self.base_cost_by_package
        extra_cost = self.extra_package_costs.compute_extra_cost(n_packages)
        return base_cost + extra_cost
