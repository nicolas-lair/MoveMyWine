from dataclasses import dataclass, field
from typing import Dict
from math import ceil

import pandas as pd

from src.constant import Package
from .constant import CostType
from .abstract_cost import AbstractCost


@dataclass
class ExtraPackageCost:
    extra_package_cost: float = 0  # No cost by default
    max_free_package: int = 0  # No cost by default
    multi_package_max_fee: float = 0  # No cost by default


@dataclass
class CostByPackageCalculator(AbstractCost):
    costs_by_package: Dict[str, float] = field(default_factory=dict)
    extra_package_costs: ExtraPackageCost = ExtraPackageCost()

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

    def compute_cost(self, n_bottles, *args, **kwargs) -> float:
        n_packages = ceil(n_bottles / Package.bottle_by_package)
        base_cost = n_packages * self.base_cost_by_package
        extra_cost = self.compute_extra_package_cost(n_packages)
        return base_cost + extra_cost

    def compute_cost_by_bottle(self, *args, **kwargs) -> pd.DataFrame:
        N = 100
        cost_by_bottle = [self.compute_cost(n_bottles, *args, **kwargs) for n_bottles in range(1, N)]
        cost_by_bottle = pd.DataFrame(index=range(1, N), data=cost_by_bottle, columns=[CostType.ByPackage])
        return cost_by_bottle
