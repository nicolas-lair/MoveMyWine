from abc import ABC
from dataclasses import dataclass, field
from typing import Dict
from math import ceil
from src.constant import Package
from src.app_generics.transporter_params import ExtraPackageCost


@dataclass
class CostByPackageCalculator(ABC):
    costs_by_package: Dict[str, float] = field(default_factory=dict)
    extra_package_costs: ExtraPackageCost = ExtraPackageCost()

    @property
    def base_cost_by_package(self):
        return sum(self.costs_by_package.values())

    def compute_extra_package_cost(self, n_package):
        cost = 0
        extra_packages = (n_package - self.extra_package_costs.max_free_package)
        if extra_packages > 0:
            cost = self.extra_package_costs.extra_package_cost * extra_packages
        cost = min(cost, self.extra_package_costs.multi_package_max_fee)
        return cost

    def compute_cost(self, n_bottles):
        n_packages = ceil(n_bottles / Package.bottle_by_package)
        base_cost = n_packages * self.base_cost_by_package
        extra_cost = self.compute_extra_package_cost(n_packages)
        return base_cost + extra_cost
