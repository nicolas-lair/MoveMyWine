from collections import UserList
from dataclasses import dataclass, field
from math import ceil

from src.constant import BOTTLE, EURO_PALET_WEIGHT, BaseBottle, Package


class PaletLoadMixin:
    """Palet count shared by single and multi ref expeditions, based on their weight"""

    def n_palets(
        self, max_palet_weight: float, palet_weight: float = EURO_PALET_WEIGHT
    ) -> int:
        """
        :param max_palet_weight: max gross weight of a loaded palet, palet included
        :param palet_weight: weight of an empty palet
        """
        return ceil(self.weight / (max_palet_weight - palet_weight))


@dataclass(kw_only=True)
class SingleRefExpedition(PaletLoadMixin):
    n_bottles: int
    bottle_type: BaseBottle = BOTTLE
    package: Package | None = field(default_factory=Package)

    def add_package_type(self, package: Package):
        self.package = package

    @property
    def n_packages(self):
        bottle_package = ceil(self.n_bottles / self.package.bottle_by_package)
        return bottle_package

    @property
    def weight(self):
        n_package = self.n_packages
        return (
            self.n_bottles * self.bottle_type.weight
            + self.package.box_weight * n_package
        )

    @property
    def n_bottles_equivalent(self):
        return self.n_bottles * self.bottle_type.bottle_eq


class MultiRefExpedition(PaletLoadMixin, UserList[SingleRefExpedition]):
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
