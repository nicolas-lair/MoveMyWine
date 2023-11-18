from collections import UserList
from dataclasses import dataclass, field
from math import ceil
from typing import Optional

from srcv2.constant import Package, BaseBottle, BOTTLE


@dataclass(kw_only=True)
class SingleRefExpedition:
    n_bottles: int
    bottle_type: BaseBottle = BOTTLE
    package: Optional[Package] = field(default_factory=Package)

    def add_package_type(self, package: Package):
        self.package = package

    @property
    def n_packages(self):
        bottle_package = ceil(self.n_bottles / self.package.bottle_by_package)
        return bottle_package

    @property
    def weight(self):
        n_package = self.n_packages
        return self.n_bottles * self.bottle_type.weight + self.package.box_weight * n_package

    @property
    def n_bottles_equivalent(self):
        return self.n_bottles * self.bottle_type.bottle_eq


class MultiRefExpedition(UserList[SingleRefExpedition]):
    @property
    def weight(self):
        return sum([exp.weight for exp in self])

    @property
    def n_packages(self):
        return sum([exp.n_packages for exp in self])

    @property
    def n_bottles(self):
        return sum([exp.n_bottles for exp in self])

    @property
    def n_bottles_equivalent(self):
        return sum([exp.n_bottles_equivalent for exp in self])

    def add_ref(self, expedition: SingleRefExpedition):
        self.append(expedition)
